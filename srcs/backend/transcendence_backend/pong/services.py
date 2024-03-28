from ast            import Dict
from types          import NoneType
from typing         import Dict, Any, List
from .models        import Pong, pong_model_to_dict    
from users.models   import User, user_model_to_dict
from django.db.models import Q


def join_game(user , game_id : int):
    '''Joins user to game'''
    game = Pong.objects.get(id=game_id)
    user_games = Pong.objects.filter(Q(player1=user) | Q(player2=user))
    if game.status == 'finished':
        return False
    if user == game.player1 or user == game.player2:
        game.status = 'running'
        return True
    if game.player2 is not None:
        return False
    if user_games.filter(status='pending').exists() or user_games.filter(status='running').exists():
        return False
    game.player2 = user
    game.status = 'running'
    game.save()
    return True

def pause_game(game_id: int):
    '''Pauses game'''
    game = Pong.objects.get(id=game_id)
    if game.status == 'running':
        game.status = 'paused'
        game.save()

def resume_game(game_id: int):
    '''Resumes game'''
    game = Pong.objects.get(id=game_id)
    if game.status == 'paused':
        game.status = 'running'
        game.save()



class PongService:

    @staticmethod
    def get_games(user : User, type : str, skip : int, limit : int, me : bool = False) -> List[Dict[Any, Any]]:
        """
        Returns the games of the user
        @param user: User
        @param type: str
        @param skip: int
        @param limit: int
        @return: JsonResponse with game schema
        """
        if me:
            if type == 'all':
                games = Pong.objects.filter(Q(player1=user) | Q(player2=user)).order_by('-timestamp')[skip:skip+limit]
            elif type == 'pending':
                games = Pong.objects.filter(Q(player1=user) | Q(player2=user)).filter(status='pending').order_by('-timestamp')[skip:skip+limit]
            elif type == 'finished':
                games = Pong.objects.filter(Q(player1=user) | Q(player2=user)).filter(status='finished').order_by('-timestamp')[skip:skip+limit]
            elif type == 'running':
                games = Pong.objects.filter(Q(player1=user) | Q(player2=user)).filter(status='running').order_by('-timestamp')[skip:skip+limit]
            elif type == 'paused':
                games = Pong.objects.filter(Q(player1=user) | Q(player2=user)).filter(status='paused').order_by('-timestamp')[skip:skip+limit]
            else:
                raise Exception('Invalid type')
        else:
            if type == 'all':
                games = Pong.objects.order_by('-timestamp')[skip:skip+limit]
            elif type == 'pending':
                games = Pong.objects.filter(status='pending').order_by('-timestamp')[skip:skip+limit]
            elif type == 'finished':
                games = Pong.objects.filter(status='finished').order_by('-timestamp')[skip:skip+limit]
            elif type == 'running':
                games = Pong.objects.filter(status='running').order_by('-timestamp')[skip:skip+limit]
            elif type == 'paused':
                games = Pong.objects.filter(status='paused').order_by('-timestamp')[skip:skip+limit]
            else:
                raise Exception('Invalid type')
        return [pong_model_to_dict(game) for game in games]
    
    @staticmethod
    def check_user_already_joined(user) -> bool:
        """
        Checks if the user has already joined a game
        @param user: User
        @return: bool
        """
        if Pong.objects.filter(Q(player1=user) | Q(player2=user)).filter(status='pending').exists() or Pong.objects.filter(Q(player1=user) | Q(player2=user)).filter(status='running').exists():
            return True
        return False

    @staticmethod
    def create_game(user : User) -> Dict[Any, Any]:
        """
        Creates a game for the user and assigns them as participant
        @param user: User
        @return: JsonResponse with game schema
        """
        if PongService.check_user_already_joined(user):
            raise Exception('You have a game in progress')
        game = Pong.objects.create(player1=user)
        return pong_model_to_dict(game)
    
    @staticmethod
    def get_game_by_id(game_id : int) -> Dict[Any, Any]:
        """
        Returns the game by id
        @param game_id: int
        @return: JsonResponse with game schema
        """
        game = Pong.objects.filter(id=game_id).first()
        if game is None:
            raise Exception('Game not found')
        return pong_model_to_dict(game)
    

    @staticmethod
    def join_game(user : User, game_id : int) -> Dict[Any, Any]:
        """
        Joins the user to the game
        @param user: User
        @param game_id: int
        @return: JsonResponse with game schema
        """
        game = Pong.objects.filter(id=game_id).first()
        if game is None:
            raise Exception('Game not found')
        if game.status != 'pending':
            raise Exception('Game already running')
        if game.players.filter(Q(player1=user) | Q(player2=user)).exists() and game.player2 is not None == 2:
            raise Exception('User already joined')
        if PongService.check_user_already_joined(user) and game.player2 is not None:
            raise Exception('You have a game in progress')
        if not game.player1 == user and game.player2 is None:  
            game.players.add(user)
            game.save()
        return pong_model_to_dict(game)
    

    @staticmethod
    def finish_game(game_id: int, result: Dict[str,Any] | NoneType = None) -> Dict[Any, Any]:
        """
        Finishes the game
        @param game_id: int
        @return: JsonResponse with game schema
        """
        if result is not None:
            score1 = result['s1']
            score2 = result['s2']
            left = result['left']
            right = result['right']
        else:
            score1 = 0
            score2 = 0
            left = None
            right = None
        game = Pong.objects.filter(id=game_id).first()
        if game is None:
            raise Exception('Game not found')
        game.score1 = score1
        game.score2 = score2
        game.status = 'finished'
        game.save()
        if score1 > score2:
            return user_model_to_dict(game.player1, avatar=False)
        elif score1 < score2:
            return user_model_to_dict(game.player2, avatar=False)
        return pong_model_to_dict(game)
    
    @staticmethod
    def delete_game(game_id : int, user : User) -> None:
        """
        Deletes the game
        @param game_id: int
        """
        game = Pong.objects.filter(id=game_id).first()
        if not game:
            raise Exception('Game not found')
        if game.player1 == user or game.player2 == user and game.status == 'pending':
            game.delete()
            return pong_model_to_dict(game)
        else:
            raise Exception('You are either not a participant or the game has already started')
        
        
