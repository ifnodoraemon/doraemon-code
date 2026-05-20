"""
Scheduled Task System

Enables scheduling tasks to run at intervals or specific times.
Integrates with BackgroundTaskManager for execution.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from src.core.background_tasks import get_task_manager

logger = logging.getLogger(__name__)

@dataclass
class ScheduledTask:
    """A task that is scheduled to run periodically."""
    id: str
    name: str
    description: str
    command: str  # The command or goal to execute
    interval_seconds: int | None = None
    cron_expression: str | None = None
    last_run: float | None = None
    next_run: float | None = None
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "command": self.command,
            "interval_seconds": self.interval_seconds,
            "cron_expression": self.cron_expression,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

class ScheduledTaskManager:
    """Manages recurring tasks and their persistence."""

    def __init__(self, project_dir: Path | None = None):
        self.project_dir = project_dir or Path.cwd()
        self.schedules_file = self.project_dir / ".agent" / "schedules.json"
        self._schedules: dict[str, ScheduledTask] = {}
        self._running = False
        self._loop_task: asyncio.Task | None = None

    def load_schedules(self):
        """Load schedules from persistence."""
        if not self.schedules_file.exists():
            return

        try:
            data = json.loads(self.schedules_file.read_text())
            for sid, sdata in data.items():
                self._schedules[sid] = ScheduledTask(**sdata)
        except Exception as e:
            logger.error("Failed to load schedules: %s", e)

    def save_schedules(self):
        """Save schedules to persistence."""
        self.schedules_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {sid: s.to_dict() for sid, s in self._schedules.items()}
            self.schedules_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error("Failed to save schedules: %s", e)

    def add_schedule(self, name: str, description: str, command: str, 
                     interval_seconds: int | None = None, 
                     cron_expression: str | None = None) -> str:
        """Add a new scheduled task."""
        import uuid
        sid = uuid.uuid4().hex[:8]
        
        # Calculate initial next_run
        next_run = time.time()
        if interval_seconds:
            next_run += interval_seconds
        
        task = ScheduledTask(
            id=sid,
            name=name,
            description=description,
            command=command,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            next_run=next_run
        )
        self._schedules[sid] = task
        self.save_schedules()
        return sid

    def list_schedules(self) -> list[ScheduledTask]:
        """List all schedules."""
        return list(self._schedules.values())

    def remove_schedule(self, sid: str) -> bool:
        """Remove a schedule."""
        if sid in self._schedules:
            del self._schedules[sid]
            self.save_schedules()
            return True
        return False

    async def start(self):
        """Start the scheduler loop."""
        if self._running:
            return
        
        self.load_schedules()
        self._running = True
        self._loop_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduled task manager started")

    async def stop(self):
        """Stop the scheduler loop."""
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduled task manager stopped")

    async def _scheduler_loop(self):
        """Main loop that checks and triggers tasks."""
        while self._running:
            now = time.time()
            to_trigger = []

            for sid, s in self._schedules.items():
                if not s.enabled or not s.next_run:
                    continue
                
                if now >= s.next_run:
                    to_trigger.append(s)

            for s in to_trigger:
                await self._trigger_task(s)

            await asyncio.sleep(10)  # Check every 10 seconds

    async def _trigger_task(self, s: ScheduledTask):
        """Trigger a scheduled task by handing it to BackgroundTaskManager."""
        logger.info("Triggering scheduled task: %s (%s)", s.name, s.id)
        
        bg_manager = get_task_manager()
        
        # In a real system, we'd probably call LeadAgentRuntime.execute(s.command)
        # For now, we'll just log it as a placeholder or execute a simple command if it's a RUN directive
        
        # Update run times
        s.last_run = time.time()
        if s.interval_seconds:
            s.next_run = s.last_run + s.interval_seconds
        else:
            # Simple cron approximation for "every minute" etc if we had a parser
            s.next_run = s.last_run + 60 
        
        self.save_schedules()

        # Dummy execution for demonstration
        async def run_scheduled_goal():
            # This should ideally call the Agent's orchestration or execution logic
            # For this Phase 2, we just ensure the infrastructure is there.
            await asyncio.sleep(1)
            return f"Scheduled task '{s.name}' executed."

        await bg_manager.start_task(
            name=f"Scheduled: {s.name}",
            description=s.description,
            coroutine=run_scheduled_goal()
        )

# Global instance
_scheduler: ScheduledTaskManager | None = None

def get_scheduler(project_dir: Path | None = None) -> ScheduledTaskManager:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = ScheduledTaskManager(project_dir)
    return _scheduler
