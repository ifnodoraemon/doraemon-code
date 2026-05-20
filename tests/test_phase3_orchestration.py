import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.core.planner import TaskPlanner, ExecutionPlan
from src.core.planner.planner_output import TaskStatus

@pytest.mark.asyncio
async def test_refine_plan_mock():
    # Mock model client for re-planning
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = """
    {
      "tasks": [
        {
          "id": "t1",
          "title": "Setup",
          "description": "Initial setup",
          "status": "completed",
          "dependencies": []
        },
        {
          "id": "new_t2",
          "title": "Refined Build",
          "description": "Adjusted build task based on feedback",
          "priority": "high",
          "complexity": 3,
          "estimated_minutes": 30,
          "dependencies": ["t1"]
        }
      ]
    }
    """
    mock_client.chat.return_value = mock_response

    planner = TaskPlanner(model_client=mock_client)
    
    # Create initial plan
    from src.core.planner.planner_output import Task, TaskPriority
    initial_tasks = [
        Task(id="t1", title="Setup", description="...", status=TaskStatus.COMPLETED),
        Task(id="t2", title="Build", description="...", status=TaskStatus.PENDING)
    ]
    initial_plan = ExecutionPlan(
        id="p1", 
        goal="Test", 
        tasks=initial_tasks,
        total_estimated_minutes=60,
        total_complexity=3,
        high_risk_count=0
    )

    refined_plan = await planner.refine_plan(initial_plan, "Task t2 failed because of X")

    assert len(refined_plan.tasks) == 2
    assert refined_plan.tasks[0].id == "t1"
    assert refined_plan.tasks[1].id != "t2" # Should be a new ID or updated ID
    assert "Refined" in refined_plan.tasks[1].title

@pytest.mark.asyncio
async def test_merge_engine():
    from src.runtime.merge_engine import OrchestrationMergeEngine
    engine = OrchestrationMergeEngine()
    
    engine.add_worker_output("t1", "Done setup", ["file1.txt"])
    engine.add_worker_output("t2", "Done build", ["file1.txt", "file2.txt"])
    
    result = engine.merge_results()
    assert "file1.txt" in result.conflicts
    assert "Done setup" in result.summary
    assert "Done build" in result.summary
