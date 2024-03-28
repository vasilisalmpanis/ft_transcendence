from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws$", consumers.PongConsumer.as_asgi()),
]

pong_channels = {
    consumers.PongRunner.alias: consumers.PongRunner.as_asgi(),
}
