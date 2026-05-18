"""Execution loop for the computer-use agent demo."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .browser_tools import BrowserSession
from .models import BrowserAction, StepRecord
from .planners import LlmPlanner, Planner, ScriptedCrmPlanner
from .trace import TraceWriter

PlannerMode = Literal["scripted", "llm"]


@dataclass
class RunResult:
    run_id: str
    success: bool
    summary: str
    trace_dir: Path
    report_path: Path
    downloads: list[str]
    steps: list[StepRecord]
    video_path: Path | None = None


class ComputerUseRunner:
    """Runs planner-selected browser actions with trace and failure boundaries."""

    def __init__(
        self,
        *,
        goal: str,
        start_url: str,
        planner_mode: PlannerMode = "scripted",
        trace_dir: Path = Path("/tmp/computer-use-agent-traces"),
        headless: bool = True,
        max_steps: int = 20,
        max_step_retries: int = 2,
        month: str = "2026-05",
        record_video: bool = False,
    ) -> None:
        self.goal = goal
        self.start_url = start_url
        self.planner_mode = planner_mode
        self.trace = TraceWriter(trace_dir)
        self.headless = headless
        self.max_steps = max_steps
        self.max_step_retries = max_step_retries
        self.month = month
        self.record_video = record_video

    async def run(self) -> RunResult:
        planner = self._make_planner()
        browser = BrowserSession(
            self.trace,
            headless=self.headless,
            record_video=self.record_video,
            allowed_origin=self.start_url,
        )
        steps: list[StepRecord] = []
        downloads: list[str] = []
        observation: dict[str, Any] = {"ok": True, "payload": {}, "observation": "Run started"}
        success = False
        summary = "Run did not complete."

        await browser.start()
        try:
            for step_id in range(1, self.max_steps + 1):
                action = await planner.next_action(observation)
                if action.done:
                    success = True
                    summary = action.final_summary or "Planner marked the run complete."
                    break

                record, observation = await self._execute_with_retry(browser, step_id, action)
                steps.append(record)
                if record.download_path:
                    downloads.append(record.download_path)
                if not record.ok:
                    summary = f"Step {step_id} failed: {record.error or record.observation}"
                    break
            else:
                summary = f"Stopped after max_steps={self.max_steps}."
        finally:
            await browser.close()

        report_path = self.trace.write_report(
            goal=self.goal,
            success=success,
            summary=summary,
            steps=steps,
            downloads=downloads,
            video_path=str(browser.video_path) if browser.video_path else None,
        )
        return RunResult(
            run_id=self.trace.run_id,
            success=success,
            summary=summary,
            trace_dir=self.trace.root,
            report_path=report_path,
            downloads=downloads,
            steps=steps,
            video_path=browser.video_path,
        )

    async def _execute_with_retry(
        self,
        browser: BrowserSession,
        step_id: int,
        action: BrowserAction,
    ) -> tuple[StepRecord, dict[str, Any]]:
        last_record: StepRecord | None = None
        last_observation: dict[str, Any] = {}
        for attempt in range(self.max_step_retries + 1):
            started = time.monotonic()
            result = await browser.execute(step_id, action)
            duration_ms = int((time.monotonic() - started) * 1000)
            record = StepRecord(
                step_id=step_id,
                tool=action.tool,
                args=action.args,
                expected_observation=action.expected_observation,
                ok=result.ok,
                observation=result.observation,
                duration_ms=duration_ms,
                screenshot_path=result.screenshot_path,
                download_path=result.download_path,
                error=result.error,
            )
            self.trace.write_step(record)
            last_record = record
            last_observation = {
                "ok": result.ok,
                "observation": result.observation,
                "payload": result.payload,
                "error": result.error,
                "attempt": attempt + 1,
            }
            if result.ok:
                return record, last_observation
        return last_record, last_observation

    def _make_planner(self) -> Planner:
        if self.planner_mode == "llm":
            return LlmPlanner(goal=self.goal, start_url=self.start_url)
        return ScriptedCrmPlanner(start_url=self.start_url, month=self.month)
