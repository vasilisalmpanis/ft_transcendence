from ast                        import mod
from email.policy               import default
from http                       import server
from django.db                  import models
from users.models.users         import User
from django.utils               import timezone
from typing                     import Any, Dict

# Create your models here.


class Chat(models.Model):
    id = models.AutoField(primary_key=True)
    participants = models.ManyToManyField(User, related_name="chats")
    name = models.CharField(max_length=255, null=True, blank=True)
    class Meta:
        verbose_name = 'Chat'
        verbose_name_plural = 'Chats'


def chat_model_to_dict(chat : "Chat") -> Dict[Any,Any]:
    """
    Convert chat model to dict
    :param chat: Chat instance
    :return: dict
    """
    if not chat:
        return {}
    participants = chat.participants.all()
    if participants is None:
        return {}
    return {
        "id": chat.id,
        "name": chat.name,
        "participants": { participant.username: participant.id for participant in participants },
    }


class Message(models.Model):
    id = models.AutoField(primary_key=True)
    chat_id = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    timestamp = models.DateTimeField(default=timezone.now)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    read = models.BooleanField(default=False)
    content = models.TextField()

    def get_messages(chat_id, skip=0, limit=10) -> list:
        messages = Message.objects.filter(chat_id=chat_id).order_by("-timestamp")[skip:skip+limit]
        return [
            {
                "id": message.id,
                "chat_id": message.chat_id.id,
                "timestamp": message.timestamp,
                "sender": message.sender.username,
                "content": message.content,
                "read": message.read
            }
            for message in messages
        ]
    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

