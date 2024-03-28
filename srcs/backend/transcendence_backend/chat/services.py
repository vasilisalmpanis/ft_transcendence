from calendar import c
from re import A
from .models        import Chat, Message, chat_model_to_dict
from users.models   import User
from typing         import List, Dict



class ChatService:
    @staticmethod
    def get_chat_id(user : User, user_id : int) -> int:
        """
        Get ID of chat between two users
        :param user: User instance
        :param user_id: int
        :return: int
        """
        chat = Chat.objects.filter(participants__id=user.id).filter(participants__id=user_id).first()
        if chat:
            return chat.id
        return None
    
    @staticmethod
    def create_chat(sender : User, user_id, name=None) -> Dict[str, str]:
        """
        Create chat between two users
        :param user: User instance
        :param user_id: int
        :param name: str
        :return: Chat instance
        """
        if sender.id == user_id:
            raise ValueError("Cannot create chat with self")
        receiver = User.objects.get(id=user_id)
        if not receiver:
            raise ValueError("Receiver not found")
        if not sender.friends.filter(id=user_id).exists():
            raise ValueError("User is not your friend")
        if not name:
            name = f"{sender.username} and {receiver.username} chat"
        chat = Chat.objects.create(name=name)
        chat.participants.add(sender)
        chat.participants.add(receiver)
        return chat_model_to_dict(chat)
    
    @staticmethod
    def delete_chat(user : User, chat_id : int) -> Dict[str, str]:
        """
        Delete chat by ID
        :param chat_id: int
        :return: bool
        """
        chat = Chat.objects.filter(id=chat_id, participants__id=user.id).first()
        if chat:
            response = chat_model_to_dict(chat)
            chat.delete()
            return response
        return {}
    
    @staticmethod
    def get_chats(user : User, skip : int = 0, limit : int = 10) -> List[Dict[str, str]]:
        """
        Get all chats for a user
        :param user: User instance
        :param skip: int
        :param limit: int
        :return: list
        """
        chats = Chat.objects.filter(participants__id=user.id)[skip:skip+limit]
        return [
                    chat_model_to_dict(chat)
                    for chat in chats
                    ]
        