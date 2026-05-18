from pathlib import Path

import pytest
from pydantic import ValidationError

from examples.computer_use_agent.browser_tools import BrowserSession
from examples.computer_use_agent.models import BrowserAction, StepRecord
from examples.computer_use_agent.planners import ScriptedCrmPlanner
from examples.computer_use_agent.trace import TraceWriter


def test_browser_action_accepts_whitelisted_tool():
    action = BrowserAction.model_validate(
        {
            "tool": "browser_click",
            "args": {"testid": "login-submit"},
            "expected_observation": "dashboard visible",
        }
    )

    assert action.tool == "browser_click"


def test_browser_action_rejects_unknown_tool():
    with pytest.raises(ValidationError):
        BrowserAction.model_validate({"tool": "shell_run", "args": {}})


def test_browser_session_restricts_open_url_to_allowed_origin(tmp_path: Path):
    browser = BrowserSession(
        TraceWriter(tmp_path, run_id="run-1"),
        allowed_origin="http://127.0.0.1:8765/",
    )

    assert browser._is_allowed_url("http://127.0.0.1:8765/dashboard") is True
    assert browser._is_allowed_url("http://127.0.0.1:9999/dashboard") is False
    assert browser._is_allowed_url("https://127.0.0.1:8765/dashboard") is False
    assert browser._is_allowed_url("https://example.com/") is False


def test_trace_writer_writes_steps_and_report(tmp_path: Path):
    trace = TraceWriter(tmp_path, run_id="run-1")
    record = StepRecord(
        step_id=1,
        tool="browser_snapshot",
        args={},
        expected_observation="snapshot captured",
        ok=True,
        observation="Captured page snapshot",
        duration_ms=12,
    )

    trace.write_step(record)
    report = trace.write_report(
        goal="test goal",
        success=True,
        summary="done",
        steps=[record],
        downloads=[],
    )

    assert trace.steps_path.read_text(encoding="utf-8").count("browser_snapshot") == 1
    assert report.read_text(encoding="utf-8").startswith("# Computer-Use Agent Report")


@pytest.mark.asyncio
async def test_scripted_planner_adds_dynamic_customer_actions():
    planner = ScriptedCrmPlanner(start_url="http://127.0.0.1:8765/", month="2026-05")

    for _ in range(8):
        await planner.next_action({"payload": {}})

    first_dynamic = await planner.next_action(
        {"payload": {"customer_ids": ["cust-001", "cust-002"]}}
    )
    second_dynamic = await planner.next_action({"payload": {}})

    assert first_dynamic.args["testid"] == "mark-followed-cust-001"
    assert second_dynamic.args["testid"] == "mark-followed-cust-002"


@pytest.mark.asyncio
async def test_crm_app_api_flow():
    import httpx

    pytest.importorskip("fastapi")
    from examples.computer_use_agent.crm_app import create_app

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/login",
            json={"username": "agent@example.com", "password": "demo-password"},
        )
        assert login.json()["ok"] is True

        health = await client.get("/api/health")
        assert health.json() == {"app": "computer-use-agent-crm-demo"}

        pending = await client.get("/api/customers?month=2026-05&status=PENDING")
        assert len(pending.json()["items"]) == 2

        update = await client.patch(
            "/api/customers/cust-001/status",
            json={"status": "FOLLOWED_UP"},
        )
        assert update.json()["customer"]["status"] == "FOLLOWED_UP"

        export = await client.get("/api/export?month=2026-05")
        assert "cust-001" in export.text
        assert "FOLLOWED_UP" in export.text
