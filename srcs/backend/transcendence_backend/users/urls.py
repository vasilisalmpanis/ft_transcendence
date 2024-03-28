from django.urls import path
from users.views import user_views, friends_views

urlpatterns = [
    path("healthcheck", user_views.health_check, name="health_check"),

    path("users", user_views.UserView.as_view(), name="users"),
    path("users/me", user_views.CurrentUserView.as_view(), name="get_current_user"),
    path("users/<int:id>", user_views.user_by_id_view, name="user_by_id"),
    path("users/<str:username>", user_views.user_by_username_view, name="user_by_id"),
    path("block", user_views.BlockedUsersView.as_view(), name="block_user"),

    path("friends", user_views.get_friends, name="get_friends"), # Could be changed to /users/me/friends
    path("friendrequests/incoming", friends_views.get_incoming_friend_requests, name="get_pending_friend_requests"),
    path("friendrequests", friends_views.FriendsView.as_view() , name="friend_requests"),
    path("friendrequests/accept", friends_views.accept_friend_request, name="accept_friend_request"),
    path("friendrequests/decline", friends_views.decline_friend_request, name="decline_friend_request"),
    path("unfriend", friends_views.unfriend, name="unfriend"),

    path("2fa", user_views.TOPTView.as_view(), name="2fa"),
    path("2fa/verify", user_views.verify_2fa_code, name="verify_2fa"),
]       
