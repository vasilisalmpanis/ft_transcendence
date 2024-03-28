from .views         import TournamentView
from django.urls    import path


urlpatterns = [
    path('tournaments', TournamentView.as_view(), name='tournaments'),
]