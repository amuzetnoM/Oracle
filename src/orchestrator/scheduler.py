"""
Scheduler

Task scheduling for periodic and one-time operations.
"""

from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
import threading


class TaskStatus(Enum):
    """Task execution statuses."""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    task_id: str
    name: str
    callback: Callable
    interval_seconds: Optional[float] = None  # None for one-time tasks
    next_run: datetime = field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    status: TaskStatus = TaskStatus.SCHEDULED
    run_count: int = 0
    max_runs: Optional[int] = None  # None for unlimited
    args: tuple = field(default_factory=tuple)
    kwargs: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


class Scheduler:
    """
    Task scheduler for periodic and one-time operations.
    
    Provides cron-like scheduling capabilities.
    """
    
    def __init__(self):
        """Initialize scheduler."""
        self.logger = logging.getLogger(__name__)
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._task_counter = 0
    
    def schedule_task(
        self,
        name: str,
        callback: Callable,
        interval_seconds: Optional[float] = None,
        delay_seconds: float = 0,
        max_runs: Optional[int] = None,
        args: tuple = (),
        kwargs: Optional[Dict] = None
    ) -> str:
        """
        Schedule a task.
        
        Args:
            name: Task name
            callback: Function to call
            interval_seconds: Repeat interval (None for one-time)
            delay_seconds: Initial delay before first run
            max_runs: Maximum number of runs (None for unlimited)
            args: Positional arguments for callback
            kwargs: Keyword arguments for callback
        
        Returns:
            Task ID
        """
        self._task_counter += 1
        task_id = f"task_{self._task_counter}"
        
        next_run = datetime.now() + timedelta(seconds=delay_seconds)
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            callback=callback,
            interval_seconds=interval_seconds,
            next_run=next_run,
            max_runs=max_runs,
            args=args,
            kwargs=kwargs or {}
        )
        
        self.tasks[task_id] = task
        self.logger.info(f"Scheduled task: {name} (ID: {task_id})")
        
        return task_id
    
    def schedule_daily(
        self,
        name: str,
        callback: Callable,
        hour: int = 0,
        minute: int = 0,
        args: tuple = (),
        kwargs: Optional[Dict] = None
    ) -> str:
        """
        Schedule a daily task at specific time.
        
        Args:
            name: Task name
            callback: Function to call
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            args: Positional arguments
            kwargs: Keyword arguments
        
        Returns:
            Task ID
        """
        # Calculate next run time
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if next_run <= now:
            next_run += timedelta(days=1)
        
        delay = (next_run - now).total_seconds()
        
        return self.schedule_task(
            name=name,
            callback=callback,
            interval_seconds=86400,  # 24 hours
            delay_seconds=delay,
            args=args,
            kwargs=kwargs
        )
    
    def schedule_every(
        self,
        name: str,
        callback: Callable,
        minutes: Optional[int] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None,
        args: tuple = (),
        kwargs: Optional[Dict] = None
    ) -> str:
        """
        Schedule a recurring task.
        
        Args:
            name: Task name
            callback: Function to call
            minutes: Interval in minutes
            hours: Interval in hours
            days: Interval in days
            args: Positional arguments
            kwargs: Keyword arguments
        
        Returns:
            Task ID
        """
        interval = 0
        if minutes:
            interval += minutes * 60
        if hours:
            interval += hours * 3600
        if days:
            interval += days * 86400
        
        if interval == 0:
            raise ValueError("Must specify at least one time interval")
        
        return self.schedule_task(
            name=name,
            callback=callback,
            interval_seconds=interval,
            args=args,
            kwargs=kwargs
        )
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: Task ID
        
        Returns:
            True if successful
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.status = TaskStatus.CANCELLED
        self.logger.info(f"Cancelled task: {task.name} (ID: {task_id})")
        
        return True
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """
        Get task by ID.
        
        Args:
            task_id: Task ID
        
        Returns:
            ScheduledTask or None
        """
        return self.tasks.get(task_id)
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[ScheduledTask]:
        """
        List all tasks, optionally filtered by status.
        
        Args:
            status: Optional status filter
        
        Returns:
            List of tasks
        """
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        return tasks
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            self.logger.warning("Scheduler already running")
            return
        
        self.running = True
        self._scheduler_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._scheduler_thread.start()
        self.logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            return
        
        self.running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        self.logger.info("Scheduler stopped")
    
    def _run_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                self._check_and_run_tasks()
                time.sleep(1)  # Check every second
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
    
    def _check_and_run_tasks(self):
        """Check for tasks ready to run and execute them."""
        now = datetime.now()
        
        for task in self.tasks.values():
            if task.status == TaskStatus.CANCELLED:
                continue
            
            if task.status == TaskStatus.RUNNING:
                continue
            
            # Check if max runs reached
            if task.max_runs and task.run_count >= task.max_runs:
                task.status = TaskStatus.COMPLETED
                continue
            
            # Check if it's time to run
            if now >= task.next_run:
                self._run_task(task)
    
    def _run_task(self, task: ScheduledTask):
        """Execute a task."""
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.now()
        
        self.logger.debug(f"Running task: {task.name}")
        
        # Run in separate thread to avoid blocking scheduler
        thread = threading.Thread(
            target=self._execute_task,
            args=(task,),
            daemon=True
        )
        thread.start()
    
    def _execute_task(self, task: ScheduledTask):
        """Execute task callback."""
        try:
            task.callback(*task.args, **task.kwargs)
            task.run_count += 1
            task.status = TaskStatus.SCHEDULED
            
            # Schedule next run
            if task.interval_seconds:
                task.next_run = datetime.now() + timedelta(
                    seconds=task.interval_seconds
                )
            else:
                # One-time task
                task.status = TaskStatus.COMPLETED
            
            self.logger.debug(f"Task completed: {task.name}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            self.logger.error(f"Task failed: {task.name}: {e}")
