"""
ASGI config for api project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from channels.auth                  import AuthMiddlewareStack
from channels.routing               import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from channels.security.websocket    import AllowedHostsOriginValidator
from pong.middlewares               import AuthMiddleware
from tournament.routing             import websocket_urlpatterns as tournament_websocket_urlpatterns, tournament_channels
from django.core.asgi               import get_asgi_application

from pong.routing import websocket_urlpatterns, pong_channels

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transcendence_backend.settings')


application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddleware(URLRouter(websocket_urlpatterns + tournament_websocket_urlpatterns)),
        "channel": ChannelNameRouter({**pong_channels, **tournament_channels}),
    }
)
