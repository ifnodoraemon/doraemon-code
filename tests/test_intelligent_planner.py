import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.core.planner import TaskPlanner
from src.core.planner.planner_output import TaskPriority

@pytest.mark.asyncio
async def test_llm_decomposition():
    # Mock model client
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = """
    {
      "tasks": [
        {
          "id": "t1",
          "title": "Setup",
          "description": "Initial setup",
          "priority": "high",
          "complexity": 1,
          "estimated_minutes": 10,
          "dependencies": []
        },
        {
          "id": "t2",
          "title": "Build",
          "description": "Main build task",
          "priority": "critical",
          "complexity": 5,
          "estimated_minutes": 60,
          "dependencies": ["t1"]
        }
      ]
    }
    """
    mock_client.chat.return_value = mock_response

    planner = TaskPlanner(model_client=mock_client)
    plan = await planner.generate_plan("Build something great")

    assert len(plan.tasks) == 2
    assert plan.tasks[0].title == "Setup"
    assert plan.tasks[1].title == "Build"
    assert plan.tasks[1].dependencies[0].task_id == plan.tasks[0].id
    assert plan.tasks[1].priority == TaskPriority.CRITICAL

@pytest.mark.asyncio
async def test_fallback_decomposition():
    # Test fallback when no model client is provided
    planner = TaskPlanner(model_client=None)
    plan = await planner.generate_plan("fix a bug")

    assert len(plan.tasks) > 0
    # Pattern-based bug fix decomposition usually has 4 tasks
    assert any("reproduce" in t.title.lower() for t in plan.tasks)
