"""This module defines three distinct decorators for scheduling.
 - `scheduled_now` is only there for debugging purpose: the decorated method
   is executed as is
 - `scheduled_thread` starts the decorated method as a new thread, but does not
   really "follow" it
 - `scheduled_celery` ensures tasks management via Celery, but is preferable not
   to use while in debugging mode

Note that it is strongly discouraged to use database objects (model instances,
etc.) as parameters of methods decorated with those decorators.

Prefer using built-in types, such as `float`, `str`, `dict` (for a complete
list, see https://docs.python.org/3/library/stdtypes.html).
"""


def scheduled_now(func):
    """Provides a decorator to execute the task right away.
    Mostly useful for debugging purpose.
    """
    return func


import threading
def scheduled_thread(func):
    """Provides a decorator to schedule a task as a new thread.
    Problem: an unexpected shutdown may lose the task forever...
    """
    def go(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
    return go


from celery import shared_task
def scheduled_celery(func):
    """Provides a decorator to schedule a task with Celery.
    """
    def go(*args, **kwargs):
        func.apply_async(args=args, kwargs=kwargs)
        #shared_task(func).apply_async(args=args, kwargs=kwargs)
    return go


from django.conf import settings
if settings.DEBUG:
    # scheduled = scheduled_now
    scheduled = scheduled_thread
else:
    scheduled = scheduled_celery
