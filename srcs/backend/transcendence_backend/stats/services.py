from typing import Dict, List
from users.models import User
from stats.models import Stats, stats_model_to_dict
import json

class StatService:
    @staticmethod
    def set_stats(user_1: str, user_2: str, score_1: int, score_2: int):
        """
        Sets the stats for the users based on the game result
        :param user_1: Username of the first user
        :param user_2: Username of the second user
        :param score_1: Score of the first user
        :param score_2: Score of the second user
        """
        user1 = User.objects.get(username=user_1)
        user2 = User.objects.get(username=user_2)
        stats1 = Stats.objects.get(user=user1)
        stats2 = Stats.objects.get(user=user2)
        stats1.games_played += 1
        stats2.games_played += 1
        if score_1 > score_2:
            stats1.games_won += 1
            stats2.games_lost += 1
            stats1.total_points += 3
            stats1.win_streaks += 1
            stats2.win_streaks = 0
        elif score_1 < score_2:
            stats2.games_won += 1
            stats1.games_lost += 1
            stats2.total_points += 3
            stats2.win_streaks += 1
            stats1.win_streaks = 0
        else:
            stats1.win_streaks = 0
            stats2.win_streaks = 0
            stats1.games_lost += 1
            stats2.games_lost += 1
        stats1.save()
        stats2.save()
    
    @staticmethod
    def create_stats(user: User):
        """
        Creates the stats for the user
        :param user: User object
        """
        stats = Stats(user=user)
        stats.save()

    @staticmethod
    def get_stats(user: User) -> Dict[str, int]:
        """
        Returns the stats for the user
        :param user: User object
        :return: Dict
        """
        stats = Stats.objects.get(user=user)
        return stats_model_to_dict(stats)
    
    @staticmethod
    def leaderboard(skip: int, limit: int, order: str) -> List[Dict[str, int]]:
        """
        Returns the leaderboard
        :param skip: int
        :param limit: int
        :param order: str
        :return: Dict
        """
        if limit > 100:
            raise ValueError("Limit too high")
        if order not in ["asc", "desc"]:
            raise ValueError("Invalid order")
        if order == "asc":
            users = Stats.objects.order_by("total_points")[skip:skip+limit]
        else:
            users = Stats.objects.order_by("-total_points")[skip:skip+limit]
        data = [
            StatService.get_stats(user.user)
            for user in users
        ]
        return data