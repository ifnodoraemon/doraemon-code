"""
Tools for scheduling tasks.
"""

import logging
from typing import Any, Optional
from src.core.scheduler import get_scheduler

logger = logging.getLogger(__name__)

async def schedule_task(
    name: str,
    description: str,
    command: str,
    interval_seconds: Optional[int] = None,
    cron_expression: Optional[str] = None
) -> str:
    """
    Schedule a task to run periodically in the background.

    Args:
        name: A unique name for the schedule
        description: What this task does
        command: The goal or command to execute (e.g., "Run unit tests")
        interval_seconds: Number of seconds between runs
        cron_expression: Standard cron expression (optional)
    """
    scheduler = get_scheduler()
    sid = scheduler.add_schedule(
        name=name,
        description=description,
        command=command,
        interval_seconds=interval_seconds,
        cron_expression=cron_expression
    )
    # Ensure scheduler is running
    if not scheduler._running:
        await scheduler.start()
        
    return f"Task scheduled successfully. ID: {sid}"

async def list_schedules() -> str:
    """List all currently active task schedules."""
    scheduler = get_scheduler()
    schedules = scheduler.list_schedules()
    if not schedules:
        return "No active schedules found."
    
    lines = ["Active Schedules:"]
    for s in schedules:
        trigger = f"every {s.interval_seconds}s" if s.interval_seconds else s.cron_expression
        status = "Enabled" if s.enabled else "Disabled"
        lines.append(f"- {s.name} ({s.id}): {s.description} | Trigger: {trigger} | Status: {status}")
    
    return "\n".join(lines)

async def cancel_schedule(schedule_id: str) -> str:
    """
    Cancel an existing task schedule.

    Args:
        schedule_id: The ID of the schedule to remove
    """
    scheduler = get_scheduler()
    if scheduler.remove_schedule(schedule_id):
        return f"Schedule {schedule_id} removed successfully."
    return f"Schedule {schedule_id} not found."
