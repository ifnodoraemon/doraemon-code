"""Shared data contracts for the computer-use agent demo."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ToolName = Literal[
    "browser_open",
    "browser_snapshot",
    "browser_click",
    "browser_fill",
    "browser_extract",
    "browser_download",
]


class BrowserAction(BaseModel):
    """Single controlled action selected by a planner."""

    model_config = ConfigDict(extra="forbid")

    tool: ToolName
    args: dict[str, Any] = Field(default_factory=dict)
    expected_observation: str = ""
    done: bool = False
    final_summary: str | None = None

    @field_validator("args")
    @classmethod
    def args_must_be_object(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("args must be an object")
        return value


class ToolResult(BaseModel):
    """Result returned by a controlled browser tool."""

    model_config = ConfigDict(extra="forbid")

    ok: bool
    observation: str
    payload: dict[str, Any] = Field(default_factory=dict)
    screenshot_path: str | None = None
    download_path: str | None = None
    error: str | None = None


class StepRecord(BaseModel):
    """Trace record for one execution step."""

    model_config = ConfigDict(extra="forbid")

    step_id: int
    tool: str
    args: dict[str, Any]
    expected_observation: str
    ok: bool
    observation: str
    duration_ms: int
    screenshot_path: str | None = None
    download_path: str | None = None
    error: str | None = None
