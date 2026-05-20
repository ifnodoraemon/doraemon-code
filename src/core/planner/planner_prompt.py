"""
Prompts and schemas for LLM-based task planning.
"""

import json

PLANNER_SYSTEM_PROMPT = """You are an expert software architect and task planner.
Your goal is to decompose a high-level coding goal into a set of discrete, actionable subtasks.

Each subtask should be independent enough to be executed by a worker agent.
You must identify dependencies between tasks to ensure a logical execution order.

Output your plan strictly in JSON format with the following structure:
{
  "tasks": [
    {
      "id": "t1",
      "title": "Short descriptive title",
      "description": "Detailed explanation of what needs to be done",
      "priority": "critical" | "high" | "medium" | "low",
      "complexity": 1-5,
      "estimated_minutes": integer,
      "dependencies": ["t0"] // list of IDs this task depends on
    }
  ]
}

PRINCIPLES:
1. Small Tasks: Break down large changes into smaller, verifiable steps.
2. Dependencies: Ensure setup or research tasks come before implementation.
3. Verification: Include testing or verification tasks for major changes.
4. Contextual: Use any provided codebase context to make tasks specific.
"""

def get_planner_user_prompt(goal: str, context: dict) -> str:
    """Generate the user prompt for the planner."""
    context_str = ""
    if context:
        context_str = f"\n\nContext:\n{context}"
    
    return f"Goal: {goal}{context_str}\n\nProduce the execution plan in JSON format."

REFINER_SYSTEM_PROMPT = """You are an expert software architect.
You need to refine an existing execution plan based on new feedback from a task execution.

Completed tasks should remain as they are.
You can modify pending tasks, add new ones, or remove ones that are no longer needed.

Output the updated plan strictly in JSON format with the same structure as the original.
{
  "tasks": [...]
}
"""

def get_refiner_user_prompt(plan: dict, feedback: str) -> str:
    """Generate the user prompt for the refiner."""
    return (
        f"Original Plan: {json.dumps(plan, indent=2)}\n\n"
        f"Execution Feedback: {feedback}\n\n"
        "Please refine the plan to address this feedback."
    )
