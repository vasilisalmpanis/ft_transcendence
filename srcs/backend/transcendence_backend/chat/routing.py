from django.urls    import re_path
from .              import consumers

websocket_urlpatterns = [
    re_path(r"ws/chat/dm/(?P<chat_id>\d+)/$", consumers.DirectMessageChatConsumer.as_asgi()),
    re_path(r"ws/chat/tournament/(?P<game_id>\d+)/$", consumers.GameChatConsumer.as_asgi()),
]
