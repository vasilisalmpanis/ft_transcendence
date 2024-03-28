from django.db          import models
from users.models       import User
from typing             import Any, Dict
class Stats(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stats')
    games_played = models.PositiveIntegerField(default=0)
    games_won = models.PositiveIntegerField(default=0)
    games_lost = models.PositiveIntegerField(default=0)
    total_points = models.PositiveIntegerField(default=0)
    win_streaks = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Stats'
        verbose_name_plural = 'Stats'


def stats_model_to_dict(stat : Stats) -> Dict[Any,Any]:
    if not stat:
        return {}
    return {
        "user_id": stat.user.id,
        "username": stat.user.username,
        "games_played": stat.games_played,
        "games_won": stat.games_won,
        "games_lost": stat.games_lost,
        "total_points": stat.total_points,
        "win_streaks": stat.win_streaks,
    }