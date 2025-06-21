"""
Mock implementation of Celery for testing environments where Celery is not available.
This provides compatibility during testing and development.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional
from unittest.mock import Mock

logger = logging.getLogger(__name__)


class MockQueue:
    """Mock queue for testing without Redis/Celery infrastructure."""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.tasks = []
        
    async def put(self, task_data: Dict[str, Any]):
        """Mock enqueue operation."""
        self.tasks.append(task_data)
        logger.debug(f"Mock task queued in {self.name}: {task_data}")
        
    async def get(self):
        """Mock dequeue operation."""
        if self.tasks:
            return self.tasks.pop(0)
        return None
        
    def size(self):
        """Get queue size."""
        return len(self.tasks)


class MockTask:
    """Mock Celery task for testing."""
    
    def __init__(self, func: Callable, name: str = None):
        self.func = func
        self.name = name or func.__name__
        self.retry_count = 0
        
    def delay(self, *args, **kwargs):
        """Mock async task execution."""
        logger.info(f"Mock task executed: {self.name}")
        try:
            # For testing, execute synchronously
            result = self.func(*args, **kwargs)
            return MockAsyncResult(result, task_id=f"mock-{self.name}-{id(self)}")
        except Exception as e:
            logger.error(f"Mock task failed: {self.name} - {e}")
            return MockAsyncResult(None, task_id=f"mock-{self.name}-{id(self)}", error=str(e))
    
    def apply_async(self, args=None, kwargs=None, **options):
        """Mock apply_async execution."""
        args = args or []
        kwargs = kwargs or {}
        return self.delay(*args, **kwargs)


class MockAsyncResult:
    """Mock Celery AsyncResult for testing."""
    
    def __init__(self, result: Any = None, task_id: str = None, error: str = None):
        self.result = result
        self.id = task_id or f"mock-task-{id(self)}"
        self.error = error
        self._state = "SUCCESS" if error is None else "FAILURE"
        
    @property
    def state(self):
        return self._state
        
    @property
    def status(self):
        return self._state
        
    def get(self, timeout=None):
        """Get task result."""
        if self.error:
            raise Exception(self.error)
        return self.result
        
    def ready(self):
        """Check if task is ready."""
        return True
        
    def successful(self):
        """Check if task was successful."""
        return self.error is None


class MockCelery:
    """Mock Celery app for testing environments."""
    
    def __init__(self, *args, **kwargs):
        self.conf = Mock()
        self.tasks = {}
        self.queues = {
            'medical_priority': MockQueue('medical_priority'),
            'image_processing': MockQueue('image_processing'),
            'notifications': MockQueue('notifications'),
            'audit_logging': MockQueue('audit_logging'),
            'default': MockQueue('default')
        }
        
        # Configure mock settings
        self.conf.task_serializer = 'json'
        self.conf.result_serializer = 'json'
        self.conf.accept_content = ['json']
        self.conf.result_expires = 3600
        self.conf.timezone = 'UTC'
        self.conf.enable_utc = True
        
        logger.info("MockCelery initialized for testing")
    
    def task(self, *args, **kwargs):
        """Mock task decorator."""
        def decorator(func):
            task_name = kwargs.get('name', func.__name__)
            mock_task = MockTask(func, task_name)
            self.tasks[task_name] = mock_task
            
            # Return the function with task methods attached
            func.delay = mock_task.delay
            func.apply_async = mock_task.apply_async
            func.name = task_name
            
            return func
        return decorator
    
    def send_task(self, name: str, args=None, kwargs=None, **options):
        """Mock send_task method."""
        if name in self.tasks:
            return self.tasks[name].delay(*(args or []), **(kwargs or {}))
        else:
            logger.warning(f"Mock task not found: {name}")
            return MockAsyncResult(None, error=f"Task {name} not found")


# Create mock celery app instance
celery_app = MockCelery('vigia_medical_mock')

# Mock queue aliases for compatibility
Queue = MockQueue

# Export for compatibility
__all__ = ['celery_app', 'MockCelery', 'MockTask', 'MockAsyncResult', 'MockQueue', 'Queue']