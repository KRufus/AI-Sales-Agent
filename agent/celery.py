from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
import django
from channels.routing import ProtocolTypeRouter, URLRouter
import ai_agent.routing
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent.settings")
django.setup()

app = Celery("agent")

app.config_from_object("django.conf:settings", namespace="CELERY")


app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(ai_agent.routing.websocket_urlpatterns)
        ),
    }
)
