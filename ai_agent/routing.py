# ai_agent/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"^ws/streams/$", consumers.StreamConsumer.as_asgi()),
]
