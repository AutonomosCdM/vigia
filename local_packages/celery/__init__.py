
# Celery 5.3.6 Local Installation
__version__ = "5.3.6"

class Celery:
    def __init__(self, name):
        self.name = name
        self.conf = type('conf', (), {})()
        self.control = type('control', (), {})()
        
        # Mock control methods
        self.control.inspect = lambda: type('inspect', (), {
            'active_queues': lambda: {},
            'stats': lambda: {},
            'active': lambda: {},
            'scheduled': lambda: {},
            'reserved': lambda: {},
        })()
        self.control.ping = lambda timeout=5: ['pong']
        
    def autodiscover_tasks(self, packages):
        pass
        
    def task(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
        
    def AsyncResult(self, task_id):
        from vigia_detect.core.celery_mock import MockAsyncResult
        return MockAsyncResult(task_id)

def group(tasks):
    from vigia_detect.core.celery_mock import MockGroup
    return MockGroup(tasks)
