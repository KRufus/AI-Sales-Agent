# agent/asgi.py

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import ai_agent.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent.settings")
django.setup()

from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),  # Django's ASGI application to handle traditional HTTP requests
        "websocket": AuthMiddlewareStack(
            URLRouter(ai_agent.routing.websocket_urlpatterns)
        ),
    }
)
