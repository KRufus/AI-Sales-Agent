
from django.urls import re_path
from .utils.websocket_consumer import TwilioDeepgramConsumer

websocket_urlpatterns = [
    re_path(r'^ws/proxy/$', TwilioDeepgramConsumer.as_asgi()),
]
