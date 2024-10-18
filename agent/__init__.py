from __future__ import absolute_import, unicode_literals

# This ensures that Celery is always imported when
# Django starts, allowing tasks to be registered correctly.
from .celery import app as celery_app

__all__ = ('celery_app',)