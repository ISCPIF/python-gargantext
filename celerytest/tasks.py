from celery import task
from celery.contrib.methods import task_method
from celery import current_app


class Test(object):
    @current_app.task(filter=task_method)
    def addition(self, x, y):
        #return "hello"
        return int(x) + int(y)

@current_app.task()
def add(x, y):
    return x + y

