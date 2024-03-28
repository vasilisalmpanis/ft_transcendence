from .models            import Tournament, tournament_model_to_dict
from users.models       import User
from django.db.models   import Q
from typing             import List, Dict, Any, Union

class TournamentService:
    @staticmethod
    def create_tournament(name: str, user: User, **kwargs) -> Dict[Any, Any]:
        """
        Creates a tournament
        @param name: str
        @param description: str
        @param max_players: int
        @param winner: User
        """
        if Tournament.objects.filter(name=name).exists() and name != "Pong Tournament":
            raise Exception("Tournament already exists")
        if Tournament.objects.filter(players=user, status='open').exists():
            raise Exception("User already in a tournament")
        tournament = Tournament.objects.create(name=name, **kwargs)
        tournament.players.add(user)
        tournament.save()
        return tournament_model_to_dict(tournament)
    
    @staticmethod
    def leave_tournament(user: User, tournament_id: int) -> Dict[Any, Any]:
        """
        Leaves tournament
        @param user: User
        @param tournament_id: int
        """
        tournament = Tournament.objects.get(id=tournament_id)
        if tournament.status != 'open':
            raise Exception("Tournament is closed")
        if not Tournament.objects.filter(players=user, status='open').exists():
            raise Exception("User not in a tournament")
        tournament.players.remove(user)
        tournament.save()
        return tournament_model_to_dict(tournament)
    
    @staticmethod
    def get_tournaments(type: str, skip: int, limit: int) -> List[Dict[Any, Any]]:
        """
        Returns the tournaments
        @param type: str
        @param skip: int
        @param limit: int
        @return: JsonResponse with tournament schema
        """
        if type == 'all':
            tournaments = Tournament.objects.order_by('-created_at')[skip:skip+limit]
        elif type == 'open':
            tournaments = Tournament.objects.filter(status='open').filter(players__isnull=False).order_by('-created_at')[skip:skip+limit]
        elif type == 'closed':
            tournaments = Tournament.objects.filter(status='closed').order_by('-created_at')[skip:skip+limit]
        else:
            return []
        return [tournament_model_to_dict(tournament) for tournament in tournaments]


    @staticmethod
    def update_tournament(tournament_id: int, user : User) -> Dict[Any, Any]:
        """
        Updates a tournament
        @param tournament_id: int
        @param user: User the user to add to the tournament
        :return: JsonResponse with tournament schema
        """
        tournament = Tournament.objects.get(id=tournament_id)
        if tournament.status != 'open':
            raise Exception("Tournament is closed")
        if Tournament.objects.exclude(id=tournament_id).filter(players=user).filter(Q(status='open') | Q(status='started')).exists():
            raise Exception("User already in a tournament")
        if Tournament.objects.filter(players=user, status="open").exists():
            raise Exception("User already in a tournament")
        if tournament.players.count() >= tournament.max_players:
            raise Exception("Tournament is full")
        tournament.players.add(user)
        tournament.save()
        return tournament_model_to_dict(tournament)