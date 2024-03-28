from django.db 				import models
from users.models			import User
from django.utils			import timezone
from typing					import Dict, Any

class Pong(models.Model):
	id = models.AutoField(primary_key=True)
	player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player1_games')
	player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player2_games', null=True, blank=True)
	status = models.CharField(max_length=20, default='pending')
	score1 = models.IntegerField(default=0)
	score2 = models.IntegerField(default=0)

	timestamp = models.DateTimeField(default=timezone.now)
	class Meta:
		verbose_name = 'Pong'


def pong_model_to_dict(pong : Pong) -> Dict[Any, Any]:
	return {
		'id': pong.id,
		'player1': pong.player1.username,
		'player2': pong.player2.username if pong.player2 is not None else None,
		'status': pong.status,
		'score1': pong.score1,
		'score2': pong.score2,
		'timestamp': pong.timestamp.isoformat()
	}


# class Tournaments(models.Model):
# 	id = models.AutoField(primary_key=True)
# 	participants = models.ManyToManyField(User, related_name='tournament')

# 	# 8
# 	status = models.CharField(max_length=120, default="open")

# 	# locked

# 	users = self.participants

