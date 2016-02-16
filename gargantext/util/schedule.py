"""This module defines three distinct decorators for scheduling.
"""

def scheduled_now(func):
    """Provides a decorator to execute the task right away.
    Mostly useful for debugging purpose.
    """
    return func


import threading
def scheduled_thread(func):
    """Provides a decorator to schedule a task as a new thread.
    Problem: a shutdown may lose the task forever...
    """
    def go(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
    return go



from celery import shared_task
def scheduled_celery(func):
    """Provides a decorator to schedule a task with Celery.
    """
    @shared_task
    def _func(*args, **kwargs):
        func(*args, **kwargs)
    def go(*args, **kwargs):
        _func.apply_async(args=args, kwargs=kwargs)
    return go


# scheduled = scheduled_now
# scheduled = scheduled_thread
scheduled = scheduled_celery
