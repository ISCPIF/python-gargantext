"""
Setup the Celery instance (see also gargantext/__init__.py) that will be
used by all shared_task.

This is the recommended way:
http://docs.celeryproject.org/en/3.1/django/first-steps-with-django.html
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gargantext.settings')

from django.conf import settings #noqa

app = Celery('gargantext')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
