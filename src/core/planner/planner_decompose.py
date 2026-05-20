"""
Task Decomposition Patterns

Provides pattern-based task decomposition for different goal types:
- Implementation tasks
- Bug fix tasks
- Refactoring tasks
- Testing tasks
"""

import json
import logging
from typing import Any

from src.agent.types import Message
from .planner_output import Task, TaskDependency, TaskPriority, TaskStatus
from .planner_prompt import (
    PLANNER_SYSTEM_PROMPT, 
    REFINER_SYSTEM_PROMPT,
    get_planner_user_prompt, 
    get_refiner_user_prompt
)

logger = logging.getLogger(__name__)


class TaskDecomposer:
    """Decomposes goals into task sequences based on patterns or LLM."""

    def __init__(self, id_generator):
        """
        Initialize decomposer.

        Args:
            id_generator: Function to generate unique task IDs
        """
        self._generate_id = id_generator

    async def decompose_via_llm(self, goal: str, context: dict, model_client: Any) -> list[Task]:
        """Decompose a goal into tasks using an LLM."""
        messages = [
            Message(role="system", content=PLANNER_SYSTEM_PROMPT),
            Message(role="user", content=get_planner_user_prompt(goal, context)),
        ]

        try:
            response = await model_client.chat(messages)
            content = response.content if hasattr(response, "content") else str(response)
            
            # Extract JSON if it's wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            raw_tasks = data.get("tasks", [])
            
            # Map temporary IDs to generated IDs
            id_map = {}
            for rt in raw_tasks:
                temp_id = rt.get("id", f"temp_{id(rt)}")
                id_map[temp_id] = self._generate_id()
            
            tasks = []
            for rt in raw_tasks:
                temp_id = rt.get("id")
                task = Task(
                    id=id_map.get(temp_id, self._generate_id()),
                    title=rt.get("title", "Untitled Task"),
                    description=rt.get("description", ""),
                    complexity=rt.get("complexity", 3),
                    estimated_minutes=rt.get("estimated_minutes", 30),
                    priority=self._parse_priority(rt.get("priority")),
                    status=TaskStatus.PENDING,
                )
                
                # Map dependencies
                deps = rt.get("dependencies", [])
                for dep_id in deps:
                    if dep_id in id_map:
                        task.dependencies.append(TaskDependency(id_map[dep_id], "requires"))
                
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"LLM decomposition failed: {e}")
            # Fallback will be handled by TaskPlanner
            raise
    
    def _parse_priority(self, priority_str: str | None) -> TaskPriority:
        """Parse priority string into TaskPriority enum."""
        if not priority_str:
            return TaskPriority.MEDIUM
        
        mapping = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW,
        }
        return mapping.get(priority_str.lower(), TaskPriority.MEDIUM)

    async def refine_via_llm(self, plan: Any, feedback: str, model_client: Any) -> list[Task]:
        """Refine an existing plan using an LLM based on feedback."""
        
        # Serialize plan for prompt
        plan_data = {
            "goal": plan.goal,
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status.value,
                    "dependencies": [d.task_id for d in t.dependencies]
                } for t in plan.tasks
            ]
        }

        messages = [
            Message(role="system", content=REFINER_SYSTEM_PROMPT),
            Message(role="user", content=get_refiner_user_prompt(plan_data, feedback)),
        ]

        try:
            response = await model_client.chat(messages)
            content = response.content if hasattr(response, "content") else str(response)
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            raw_tasks = data.get("tasks", [])
            
            # Map IDs (preserving existing ones)
            id_map = {}
            for t in plan.tasks:
                id_map[t.id] = t.id # Map existing IDs to themselves

            # Identify new tasks and map their temp IDs
            for rt in raw_tasks:
                temp_id = rt.get("id")
                if temp_id not in id_map:
                    id_map[temp_id] = self._generate_id()
            
            tasks = []
            for rt in raw_tasks:
                temp_id = rt.get("id")
                
                # Check if this was an existing task
                existing_task = next((t for t in plan.tasks if t.id == temp_id), None)
                
                status = TaskStatus.PENDING
                if existing_task:
                    status = existing_task.status
                
                # Overwrite status if provided in JSON (allowing LLM to force-re-run or skip)
                if "status" in rt:
                    try:
                        status = TaskStatus(rt["status"])
                    except ValueError:
                        pass

                task = Task(
                    id=id_map.get(temp_id, self._generate_id()),
                    title=rt.get("title", "Untitled Task"),
                    description=rt.get("description", ""),
                    complexity=rt.get("complexity", 3),
                    estimated_minutes=rt.get("estimated_minutes", 30),
                    priority=self._parse_priority(rt.get("priority")),
                    status=status,
                )
                
                # Map dependencies
                deps = rt.get("dependencies", [])
                for dep_id in deps:
                    if dep_id in id_map:
                        task.dependencies.append(TaskDependency(id_map[dep_id], "requires"))
                
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"LLM refinement failed: {e}")
            raise

    def create_implementation_tasks(self, goal: str, context: dict) -> list[Task]:
        """Create tasks for an implementation goal."""
        planning_task = Task(
            id=self._generate_id(),
            title="Analyze Requirements",
            description=f"Understand what needs to be built for: {goal}",
            complexity=2,
            estimated_minutes=15,
            priority=TaskPriority.HIGH,
        )

        design_task = Task(
            id=self._generate_id(),
            title="Design Solution",
            description="Plan the implementation approach and identify components",
            complexity=3,
            estimated_minutes=20,
            priority=TaskPriority.HIGH,
            dependencies=[TaskDependency(planning_task.id, "requires")],
        )

        implement_task = Task(
            id=self._generate_id(),
            title="Implement Solution",
            description=f"Write the code to: {goal}",
            complexity=4,
            estimated_minutes=60,
            priority=TaskPriority.MEDIUM,
            dependencies=[TaskDependency(design_task.id, "requires")],
            checkpoint_recommended=True,
        )

        test_task = Task(
            id=self._generate_id(),
            title="Test Implementation",
            description="Write and run tests to verify the implementation",
            complexity=2,
            estimated_minutes=20,
            priority=TaskPriority.MEDIUM,
            dependencies=[TaskDependency(implement_task.id, "requires")],
        )

        return [planning_task, design_task, implement_task, test_task]

    def create_bugfix_tasks(self, goal: str, context: dict) -> list[Task]:
        """Create tasks for a bug fix goal."""
        reproduce_task = Task(
            id=self._generate_id(),
            title="Reproduce Issue",
            description="Identify steps to reproduce the bug",
            complexity=2,
            estimated_minutes=15,
            priority=TaskPriority.HIGH,
        )

        investigate_task = Task(
            id=self._generate_id(),
            title="Investigate Root Cause",
            description="Find the source of the bug in the code",
            complexity=3,
            estimated_minutes=30,
            priority=TaskPriority.HIGH,
            dependencies=[TaskDependency(reproduce_task.id, "requires")],
        )

        fix_task = Task(
            id=self._generate_id(),
            title="Implement Fix",
            description=f"Fix: {goal}",
            complexity=3,
            estimated_minutes=30,
            priority=TaskPriority.MEDIUM,
            dependencies=[TaskDependency(investigate_task.id, "requires")],
            checkpoint_recommended=True,
        )

        verify_task = Task(
            id=self._generate_id(),
            title="Verify Fix",
            description="Confirm the fix works and doesn't break other functionality",
            complexity=2,
            estimated_minutes=15,
            priority=TaskPriority.MEDIUM,
            dependencies=[TaskDependency(fix_task.id, "requires")],
        )

        return [reproduce_task, investigate_task, fix_task, verify_task]

    def create_refactor_tasks(self, goal: str, context: dict) -> list[Task]:
        """Create tasks for a refactoring goal."""
        analyze_task = Task(
            id=self._generate_id(),
            title="Analyze Current Code",
            description="Understand the current implementation and its issues",
            complexity=2,
            estimated_minutes=20,
            priority=TaskPriority.HIGH,
        )

        plan_task = Task(
            id=self._generate_id(),
            title="Plan Refactoring",
            description="Design the target architecture and migration path",
            complexity=4,
            estimated_minutes=30,
            priority=TaskPriority.HIGH,
            dependencies=[TaskDependency(analyze_task.id, "requires")],
        )

        refactor_task = Task(
            id=self._generate_id(),
            title="Refactor Code",
            description=f"Refactor: {goal}",
            complexity=5,
            estimated_minutes=90,
            priority=TaskPriority.MEDIUM,
            dependencies=[TaskDependency(plan_task.id, "requires")],
            checkpoint_recommended=True,
        )

        test_task = Task(
            id=self._generate_id(),
            title="Run Tests",
            description="Ensure all existing tests pass after refactoring",
            complexity=2,
            estimated_minutes=20,
            priority=TaskPriority.MEDIUM,
            dependencies=[TaskDependency(refactor_task.id, "requires")],
        )

        return [analyze_task, plan_task, refactor_task, test_task]

    def create_testing_tasks(self, goal: str, context: dict) -> list[Task]:
        """Create tasks for a testing goal."""
        analyze_task = Task(
            id=self._generate_id(),
            title="Identify Test Cases",
            description="Determine what needs to be tested",
            complexity=2,
            estimated_minutes=15,
            priority=TaskPriority.HIGH,
        )

        write_task = Task(
            id=self._generate_id(),
            title="Write Tests",
            description=f"Write tests for: {goal}",
            complexity=3,
            estimated_minutes=45,
            priority=TaskPriority.MEDIUM,
            dependencies=[TaskDependency(analyze_task.id, "requires")],
        )

        run_task = Task(
            id=self._generate_id(),
            title="Run and Validate",
            description="Run tests and ensure they pass",
            complexity=1,
            estimated_minutes=10,
            priority=TaskPriority.MEDIUM,
            dependencies=[TaskDependency(write_task.id, "requires")],
        )

        return [analyze_task, write_task, run_task]

    def create_generic_task(self, goal: str, context: dict, complexity: int, time: int) -> Task:
        """Create a generic task."""
        return Task(
            id=self._generate_id(),
            title=goal[:50] + ("..." if len(goal) > 50 else ""),
            description=goal,
            complexity=complexity,
            estimated_minutes=time,
        )
