from django.urls import re_path
from .           import consumers

websocket_urlpatterns = [
    re_path(r"tournament$", consumers.TournamentConsumer.as_asgi()),
]
  

tournament_channels = {
    consumers.TournamentRunner.alias: consumers.TournamentRunner.as_asgi(),
}