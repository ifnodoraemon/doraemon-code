import pytest
import asyncio
from pathlib import Path
import os
import shutil
from src.host.mcp_registry import create_tool_registry
from src.core.scheduler import get_scheduler

@pytest.fixture
def temp_agent_dir(tmp_path):
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()
    commands_dir = agent_dir / "commands"
    commands_dir.mkdir()
    return tmp_path

@pytest.mark.asyncio
async def test_custom_command_as_tool(temp_agent_dir):
    # Create a dummy command
    command_content = """---
name: test_cmd
description: A test command
arguments:
  - TARGET
---
RUN echo "Hello $TARGET"
"""
    command_file = temp_agent_dir / ".agent" / "commands" / "test_cmd.md"
    command_file.write_text(command_content)

    # Need to mock Path.cwd() or pass project_dir to registry
    # For now, we'll manually use CommandToolRegistry
    from src.core.commands_tool import get_command_tool_registry
    from src.host.tools import ToolRegistry
    
    registry = ToolRegistry()
    cmd_registry = get_command_tool_registry(project_dir=temp_agent_dir)
    cmd_registry.attach_to_registry(registry)

    assert "test_cmd" in registry.get_tool_names()
    tool = registry._tools["test_cmd"]
    assert tool.description == "A test command"
    assert "TARGET" in tool.parameters["properties"]

@pytest.mark.asyncio
async def test_scheduler_infrastructure(temp_agent_dir):
    scheduler = get_scheduler(project_dir=temp_agent_dir)
    sid = scheduler.add_schedule(
        name="heartbeat",
        description="test heartbeat",
        command="echo ok",
        interval_seconds=1
    )
    
    assert len(scheduler.list_schedules()) == 1
    assert scheduler.list_schedules()[0].id == sid
    
    # Test removal
    scheduler.remove_schedule(sid)
    assert len(scheduler.list_schedules()) == 0

@pytest.mark.asyncio
async def test_scheduler_tool_registration():
    registry = await create_tool_registry()
    names = registry.get_tool_names()
    assert "schedule_task" in names
    assert "list_schedules" in names
    assert "cancel_schedule" in names
