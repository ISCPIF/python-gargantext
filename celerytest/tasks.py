from celery import task
from celery.contrib.methods import task_method
from celery import current_app


class Test(object):
    @current_app.task(filter=task_method)
    def addition(self):
        #return "hello"
        #return int(x) + int(y)


