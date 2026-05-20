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

