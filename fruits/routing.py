from django.urls import re_path
from .consumers import ChatConsumer, FruitConsumer

websocket_urlpatterns = [
    re_path(r'/chat/', ChatConsumer.as_asgi()),
    re_path(r'/shop/', FruitConsumer.as_asgi())
]