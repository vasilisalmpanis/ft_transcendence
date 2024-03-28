from email.policy import default
from django.db      import models
from users.models   import User, user_model_to_dict
from typing         import Dict, Any
# Create your models here.

class TournamentManager(models.Manager):
    '''TournamentManager model'''
    def create_tournament(self, name, description, max_players, winner, user: User):
        '''Creates a tournament'''
        if self.filter(name=name).exists():
            return None
        if self.filter(players=user).exists():
            return None
        tournament = self.create(name=name, description=description, max_players=max_players)
        tournament.players.add(user)
        tournament.save()
        return tournament

class Tournament(models.Model):
    '''Tournament model'''
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(default="let the games begin")
    max_players = models.IntegerField(default=20)
    status = models.CharField(max_length=50, default='open')
    winner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    games = models.ManyToManyField('pong.Pong', related_name='games')
    created_at = models.DateTimeField(auto_now_add=True)
    players = models.ManyToManyField(User, related_name='players')
    objects = TournamentManager()
    def __str__(self):
        return self.name
    

def tournament_model_to_dict(tournament: Tournament) -> Dict[str, Any]:
    '''Converts tournament model to dictionary'''
    return {
        'id': tournament.id,
        'name': tournament.name,
        'description': tournament.description,
        'max_players': tournament.max_players,
        'status': tournament.status,
        'winner': tournament.winner.id if tournament.winner else None,
        'created_at': tournament.created_at,
        'player_ids': [player.id for player in tournament.players.all()]
    }