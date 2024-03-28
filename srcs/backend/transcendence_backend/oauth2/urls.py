from django.urls import path
from . import views

urlpatterns = [
    path("oauth2/42intra", views.ft_intra_auth, name="ft_intra_auth"),
    path("oauth2/redir", views.handle_redir, name="handle_redir")
    ]