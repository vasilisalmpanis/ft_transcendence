from datetime                   import datetime
import re
import stat
from urllib import request
from .models                    import User, FriendRequest, user_model_to_dict, friend_request_model_to_dict
from django.conf                import settings
from cryptography.fernet        import Fernet
from transcendence_backend.totp import get_totp_token
from typing                     import Any, Dict, List
from channels.layers            import get_channel_layer
from asgiref.sync               import async_to_sync
from stats.services             import StatService
from chat.services              import ChatService
import os
import base64
import logging

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def create_user(username: str, password:str, email:str, intra_id=None, is_staff:bool = False, is_superuser:bool = False) -> Dict[str,Any]:
            avatar = settings.DEFAULT_AVATAR
            stats = StatService.create_stats()
            user = User.objects.create_user(username=username,
                                    password=password,
                                    email=email,
                                    avatar=avatar,
                                    stats=stats,
                                    ft_intra_id=intra_id,
                                    is_staff=is_staff,
                                    is_superuser=is_superuser)
            return user_model_to_dict(user)


    @staticmethod
    def get_all_users(user: User, skip:int = 0, limit:int = 10) -> List[Dict[str,Any]]:
        """
        Returns all users that the user should see
        :param user: User instance
        :param skip: int
        :param limit: int
        :return: list[Serialized User]
        """
        users_not_blocked_by_me = User.objects.exclude(blocked=user)
        users_not_blocked_me = User.objects.exclude(blocked_me=user)

        # Intersection of users who haven't blocked me and users whom I haven't blocked
        users = users_not_blocked_by_me.intersection(users_not_blocked_me).order_by('username')[skip:skip+limit]
        data = [
            user_model_to_dict(user_element, me=user)
            for user_element in users
        ]
        return data


    @staticmethod
    def update_user(user : User, username = None, password = None, email = None) -> Dict[str,Any]:
        """
        Update user details
        :param user: User instance
        :param username: str
        :param password: str
        :param email: str
        :param avatart: str
        :return: Updated user instance
        """
        if username:
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                raise Exception("Username already exists")
            user.username = username
        if password:
            user.set_password(password)
        if email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                raise Exception("Email already exists")
            user.email = email
        user.save()
        return user_model_to_dict(user)

    @staticmethod
    def get_friends(user, skip : int = 0, limit : int = 10, id: int | None = None) -> list[dict[str,Any]]:
        """
        Get friends of a user
        :param user: User instance
        :param skip: int
        :param limit: int
        :return: list[User]
        """
        if id:
            temp_user = User.objects.get(id=id)
            if not user:
                raise Exception("User not found")
            friends = temp_user.friends.all()[skip:skip+limit]
            return [
                user_model_to_dict(friend, me=user)
                for friend in friends
            ]
        else:
            friends = user.friends.all()[skip:skip+limit]
            return [
                user_model_to_dict(friend)
                for friend in friends
            ]
    
    @staticmethod
    def unfriend(user : User, friend_id : int) -> User:
        """
        Unfriend a user 
        :param user: User instance
        :param friend_id: int
        :return: Unfriended user instance
        """
        friend = user.friends.get(id=friend_id)
        if not friend:
            raise Exception("You are not friends with this user")
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)('0', {
            'type': 'manager.update',
            'status': 'unfriended friend_id {friend_id}',
            'sender_id': user.id,
        })
        user.friends.remove(friend)
        friend.friends.remove(user)
        return friend
    
    @staticmethod
    def block(user : User, user_id : int) -> Dict[str,Any]:
        """
        Block a user
        :param user: User instance
        :param user_id: int
        :return: Blocked user instance
        """
        user_to_block = User.objects.get(id=user_id)
        if not user_to_block:
            raise Exception("User not found")
        if user_to_block in user.friends.all():
            user.friends.remove(user_to_block)
        if user_to_block in user.blocked.all():
            raise Exception("User is already blocked")
        if user_to_block.blocked.filter(id=user.id).exists():
            raise Exception("User has already blocked you")
        if user.id == user_to_block.id:
            raise Exception("You cannot block yourself")
        user.blocked.add(user_to_block)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)('0', {
            'type': 'manager.update',
            'status': 'user {user_id} blocked',
            'sender_id': user.id,
        })
        FriendRequest.objects.filter(sender_id=user_to_block.id,
                                     receiver_id=user.id).delete()
        FriendRequest.objects.filter(sender_id=user.id,
                                        receiver_id=user_to_block.id).delete()
        ChatService.delete_chat_between_users(user, user_to_block)
        return user_model_to_dict(user_to_block, me=user)
    
    @staticmethod
    def unblock(user : User, user_id : int) -> Dict[str,Any]:
        """
        Unblock a user
        :param user: User instance
        :param user_id: int
        :return: Unblocked user instance
        """
        user_to_unblock = User.objects.get(id=user_id)
        if not user_to_unblock:
            raise Exception("User not found")
        if user_to_unblock not in user.blocked.all():
            raise Exception("User is not blocked")
        if user.id == user_to_unblock.id:
            raise Exception("You cannot unblock yourself")
        user.blocked.remove(user_to_unblock)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)('0', {
        'type': 'manager.update',
        'status': 'user {user_id} unblocked',
        'sender_id': user.id,
        })
        return user_model_to_dict(user_to_unblock)
    
    @staticmethod
    def get_blocked_users(user : User, skip : int = 0, limit : int = 10) -> List[Dict[str,Any]]:
        """
        Get blocked users of a user
        :param user: User instance
        :param skip: int
        :param limit: int
        :return: list[User]
        """
        blocked_users = user.blocked.all()[skip:skip+limit]
        return [
                user_model_to_dict(user_element, me=user)
                for user_element in blocked_users
        ]
    
    @staticmethod
    def get_user_by_id(me: User, id: int) -> Dict[str,Any]:
        """
        Get user by id
        :param user: User instance
        :param id: int
        :return: User instance
        """
        requested_user = User.objects.get(id=id)
        if not me:
            raise Exception("User not found")
        if me.blocked.filter(id=requested_user.id).exists():
            raise Exception("User blocked")
        if (requested_user.blocked.filter(id=me.id).exists()):
            raise Exception("User blocked you")
        return user_model_to_dict(requested_user, me=me)

    @staticmethod
    def get_user_by_username(me: User, username: str) -> Dict[str,Any]:
        """
        Get user by id
        :param user: User instance
        :param id: int
        :return: User instance
        """
        requested_user = User.objects.get(username=username)
        if not me:
            raise Exception("User not found")
        if me.blocked.filter(id=requested_user.id).exists():
            raise Exception("User blocked")
        if (requested_user.blocked.filter(id=me.id).exists()):
            raise Exception("User blocked you")
        return user_model_to_dict(requested_user, me=me)
    
    @staticmethod
    def update_last_login(user : User) -> User:
        """
        Update last login of a user
        :param user: User instance
        :return: Updated user instance
        """
        user.is_user_active = True
        user.last_login = datetime.now()
        user.save()
        return user
    
    @staticmethod
    def are_users_friends(user: User, friend_id: int) -> bool:
        """
        Check if two users are friends
        :param user: User instance
        :param friend_id: int
        :return: bool
        """
        if user.friends.filter(id=friend_id).exists():
            logger.info(f"{user.username} and {friend_id} are friends")
            return True
        return False

    


class SecondFactorService:
    @staticmethod
    def enable_2fa(user : User) -> bool:
        """
        Enable 2fa for a user
        :param user: User instance
        :return: bool
        """
        user.is_2fa_enabled = True
        user.save()
        return True
    
    @staticmethod
    def disable_2fa(user : User) -> bool:
        """
        Disable 2fa for a user
        :param user: User instance
        :return: bool
        """
        user.otp_secret = None
        user.is_2fa_enabled = False
        user.save()
        return True
    
    @staticmethod
    def create_otp_secret(user : User) -> str:
        """
        Create otp secret for a user
        :param user: User instance
        :return: str    
        """
        random = os.urandom(20)
        secret_key = base64.b32encode(random).decode('utf-8')
        secret_key = secret_key.strip('=')
        otp = base64.b32encode(random)
        key = settings.FERNET_SECRET.encode()
        f = Fernet(key)
        user.otp_secret = f.encrypt(secret_key.encode()).decode()
        user.save()
        return secret_key
    
    @staticmethod
    def verify_2fa(user : User, auth_code : str) -> bool:
        """
        Verify 2fa for a user
        :param user: User instance
        :param auth_code: str
        :return: bool
        """
        key = settings.FERNET_SECRET.encode()
        f = Fernet(key)
        if not user.otp_secret:
            raise Exception("2fa is not enabled")
        otp_secret = f.decrypt(user.otp_secret.encode()).decode()
        # otp_secret += '=' * (-len(otp_secret) % 8)
        otp_secret = otp_secret
        code = get_totp_token(otp_secret)
        if code != auth_code:
            raise Exception("Invalid 2fa code")
        return True
    
    @staticmethod
    def decrypt_otp_secret(user : User) -> str:
        """
        Decrypt otp secret for a user
        :param user: User instance
        :return: str
        """
        key = settings.FERNET_SECRET.encode()
        f = Fernet(key)
        if not user.otp_secret:
            raise Exception("2fa is not enabled")
        return f.decrypt(user.otp_secret.encode()).decode()


class FriendRequestService:
    @staticmethod
    def get_user_friend_requests(user : User, type : str, skip: int = 0, limit :int = 10) -> list[Dict[Any,Any]]:
        """
        Get friend requests for a user
        :param user: User instance
        :param type: str
        :return: list[FriendRequest]
        """
        if type == "sent":
            friend_requests = FriendRequest.objects.filter(sender=user, status="PENDING")[skip:skip+limit]
        else:
            friend_requests = FriendRequest.objects.filter(receiver=user, status="PENDING")[skip:skip+limit]
        return [
                    friend_request_model_to_dict(friend_request)
                    for friend_request in friend_requests
                ]
    
    @staticmethod
    def create_friend_request(sender : User, receiver_id : int, message : str = "") -> FriendRequest:
        """
        Create a friend request for a user
        :param sender: User instance
        :param receiver_id: int
        :param message: str
        :return: FriendRequest instance
        """
        if sender.id == receiver_id:
            raise Exception("You cannot send a friend request to yourself")
        receiver = User.objects.get(id=receiver_id)
        if not receiver:
            raise Exception("Receiver does not exist")
        if message == "":
            message = f"{sender.username} wants to be your friend"
        if sender.friends.filter(id=receiver_id).exists():
            raise Exception("You are already friends")
        if FriendRequest.objects.filter(sender=sender, receiver=receiver).exists():
            raise Exception("You already sent a friend request to this user")
        if receiver.blocked.filter(id=sender.id).exists():
            raise Exception("Blocked")
        if FriendRequest.objects.filter(sender=receiver, receiver=sender).exists():
            raise Exception("Friend request already exists")
        friend_request = FriendRequest.objects.create(
            sender=sender,
            receiver=receiver,
            message=message
        )
        return friend_request
    
    @staticmethod
    def friend_request_status(sender: User, receiver: User) -> str:
        """
        Get the status of a friend request
        :param sender: User instance
        :param receiver: User instance
        :return: str
        """
        friend_request = FriendRequest.objects.filter(sender=sender, receiver=receiver)
        if friend_request.exists():
            return friend_request.first().status
        return "NOT_SENT"
    
    @staticmethod
    def accept_friend_request(user : User, request_id : int) -> bool:
        """
        Accept a friend request for a user
        :param user: User instance
        :param request_id: int
        :return: bool
        """
        friend_request = FriendRequest.objects.get(id=request_id, receiver=user)
        if not friend_request:
            raise Exception("Friend request does not exist")
        if friend_request.status != "PENDING":
            raise Exception("Friend request is not pending")
        sender = friend_request.sender
        if user.blocked.filter(id=sender.id).exists():
            raise Exception("Receiver Blocked")
        if sender.blocked.filter(id=user.id).exists():
            raise Exception("Sender Blocked")   
        user.friends.add(sender)
        sender.friends.add(user)
        friend_request.status = "ACCEPTED"
        friend_request.save()
        friend_request.delete()
        return True
    
    @staticmethod
    def decline_friend_request(user : User, request_id : int) -> bool:
        """
        Declines a friend request for a user
        :param user: User instance
        :param request_id: int
        :return: bool
        """
        friend_request = FriendRequest.objects.get(id=request_id, receiver=user)
        if not friend_request:
            raise Exception("Friend request does not exist")
        if friend_request.status != "PENDING":
            raise Exception("Friend request is not pending")
        friend_request.status = "DECLINED"
        friend_request.save()
        friend_request.delete()
        return True
    
    @staticmethod
    def delete_friend_request(user : User, request_id : int) -> bool:
        """
        Deletes a friend request for a user
        :param user: User instance
        :param request_id: int
        :return: bool
        """
        try:
            friend_request = FriendRequest.objects.filter(sender=user, id=request_id).first()
            if friend_request:
                friend_request.delete()
                return True
            else:
                raise Exception("Friend request does not exist")
        except Exception as e:
            raise Exception("Error deleting friend request")
        