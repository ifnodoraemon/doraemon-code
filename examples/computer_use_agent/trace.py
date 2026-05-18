"""Trace writer for computer-use runs."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from .models import StepRecord


class TraceWriter:
    """Writes step-level artifacts for a computer-use run."""

    def __init__(self, trace_dir: Path, run_id: str | None = None) -> None:
        self.run_id = run_id or self._new_run_id()
        self.root = trace_dir / self.run_id
        self.screenshot_dir = self.root / "screenshots"
        self.video_dir = self.root / "videos"
        self.root.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.video_dir.mkdir(parents=True, exist_ok=True)
        self.steps_path = self.root / "steps.jsonl"
        self.report_path = self.root / "report.md"

    @staticmethod
    def _new_run_id() -> str:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        return f"{stamp}-{uuid.uuid4().hex[:8]}"

    def screenshot_path(self, step_id: int) -> Path:
        return self.screenshot_dir / f"step-{step_id:03d}.png"

    def write_step(self, record: StepRecord) -> None:
        with self.steps_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.model_dump(), ensure_ascii=False) + "\n")

    def write_raw_event(self, event: dict[str, Any]) -> None:
        with (self.root / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def write_report(
        self,
        *,
        goal: str,
        success: bool,
        summary: str,
        steps: list[StepRecord],
        downloads: list[str],
        video_path: str | None = None,
    ) -> Path:
        lines = [
            "# Computer-Use Agent Report",
            "",
            f"- Run ID: `{self.run_id}`",
            f"- Goal: {goal}",
            f"- Success: `{str(success).lower()}`",
            f"- Steps: {len(steps)}",
            "",
            "## Summary",
            "",
            summary,
            "",
            "## Downloads",
            "",
        ]
        if downloads:
            lines.extend(f"- `{path}`" for path in downloads)
        else:
            lines.append("- None")
        lines.extend(["", "## Video", ""])
        if video_path:
            lines.append(f"- `{video_path}`")
        else:
            lines.append("- None")
        lines.extend(["", "## Step Trace", ""])
        for step in steps:
            status = "ok" if step.ok else "failed"
            lines.append(
                f"- Step {step.step_id}: `{step.tool}` {status} in {step.duration_ms}ms"
            )
            if step.error:
                lines.append(f"  - Error: {step.error}")
            if step.screenshot_path:
                lines.append(f"  - Screenshot: `{step.screenshot_path}`")
        self.report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self.report_path
