"""Planners for the computer-use agent demo."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from pydantic import ValidationError

from src.core.llm.model_client import ModelClient

from .models import BrowserAction


class Planner(ABC):
    @abstractmethod
    async def next_action(self, observation: dict[str, Any]) -> BrowserAction:
        """Return the next browser action."""


class ScriptedCrmPlanner(Planner):
    """Deterministic planner used for smoke tests and demos without model keys."""

    def __init__(self, *, start_url: str, month: str = "2026-05") -> None:
        self.start_url = start_url
        self.month = month
        self._queue: list[BrowserAction] = [
            BrowserAction(
                tool="browser_open",
                args={"url": start_url},
                expected_observation="Login page is visible",
            ),
            BrowserAction(
                tool="browser_fill",
                args={"testid": "username", "value": "agent@example.com"},
                expected_observation="Username is entered",
            ),
            BrowserAction(
                tool="browser_fill",
                args={"testid": "password", "value": "demo-password"},
                expected_observation="Password is entered",
            ),
            BrowserAction(
                tool="browser_click",
                args={"testid": "login-submit"},
                expected_observation="CRM dashboard is visible",
            ),
            BrowserAction(
                tool="browser_fill",
                args={"testid": "month-filter", "value": month},
                expected_observation="Month filter is set",
            ),
            BrowserAction(
                tool="browser_fill",
                args={"testid": "status-filter", "value": "PENDING"},
                expected_observation="Status filter is set",
            ),
            BrowserAction(
                tool="browser_click",
                args={"testid": "apply-filters"},
                expected_observation="Pending customer table is visible",
            ),
            BrowserAction(
                tool="browser_extract",
                args={"query": "pending_customer_ids"},
                expected_observation="Pending customer ids are extracted",
            ),
        ]
        self._dynamic_loaded = False

    async def next_action(self, observation: dict[str, Any]) -> BrowserAction:
        if self._queue:
            return self._queue.pop(0)

        if not self._dynamic_loaded:
            ids = observation.get("payload", {}).get("customer_ids", [])
            for customer_id in ids:
                self._queue.append(
                    BrowserAction(
                        tool="browser_click",
                        args={"testid": f"mark-followed-{customer_id}"},
                        expected_observation=f"Customer {customer_id} is marked followed up",
                    )
                )
            self._queue.extend(
                [
                    BrowserAction(
                        tool="browser_download",
                        args={"testid": "export-csv"},
                        expected_observation="CSV export is downloaded",
                    ),
                    BrowserAction(
                        tool="browser_snapshot",
                        args={},
                        expected_observation="Final CRM state is captured",
                    ),
                ]
            )
            self._dynamic_loaded = True
            if self._queue:
                return self._queue.pop(0)

        return BrowserAction(
            tool="browser_snapshot",
            args={},
            expected_observation="Run is complete",
            done=True,
            final_summary="All pending customers for the selected month were updated and exported.",
        )


class LlmPlanner(Planner):
    """Model-backed planner constrained to the BrowserAction schema."""

    def __init__(self, *, goal: str, start_url: str, max_repair_attempts: int = 1) -> None:
        self.goal = goal
        self.start_url = start_url
        self.max_repair_attempts = max_repair_attempts
        self._client = None
        self._history: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You control a browser through a strict whitelist of tools. "
                    "Return exactly one JSON object matching this schema: "
                    "{tool,args,expected_observation,done,final_summary}. "
                    "Allowed tools: browser_open, browser_snapshot, browser_click, "
                    "browser_fill, browser_extract, browser_download. "
                    "Use data-testid when possible. Do not invent tools."
                ),
            },
            {
                "role": "user",
                "content": f"Goal: {goal}\nStart URL: {start_url}",
            },
        ]

    async def next_action(self, observation: dict[str, Any]) -> BrowserAction:
        if self._client is None:
            self._client = await ModelClient.create()

        self._history.append(
            {
                "role": "user",
                "content": "Latest observation JSON:\n"
                + json.dumps(observation, ensure_ascii=False)[:6000],
            }
        )
        response = await self._client.chat(self._history, temperature=0)
        content = response.content or ""
        for _ in range(self.max_repair_attempts + 1):
            try:
                action = BrowserAction.model_validate_json(_extract_json_object(content))
                self._history.append({"role": "assistant", "content": action.model_dump_json()})
                return action
            except (ValidationError, ValueError) as exc:
                self._history.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response did not match the required JSON schema. "
                            f"Error: {exc}. Return only one valid JSON object."
                        ),
                    }
                )
                response = await self._client.chat(self._history, temperature=0)
                content = response.content or ""
        raise ValueError("Model did not return a valid BrowserAction")


def _extract_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found")
    return stripped[start : end + 1]
