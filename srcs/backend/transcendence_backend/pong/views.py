from curses.ascii import US
from unittest import skip
from users.models                       import User
from django.http                        import JsonResponse
from transcendence_backend.decorators   import jwt_auth_required
from django.views                       import View
from .services                          import PongService
from django.utils.decorators             import method_decorator
import json
import logging

logger = logging.getLogger(__name__)
@method_decorator(jwt_auth_required(), name='dispatch')
class PongView(View):
    def get(self, request, user : User) -> JsonResponse:
        """
        Returns the games of the user
        @param request: HttpRequest
        @param user: User
        @return: JsonResponse with game schema
        """
        type = str(request.GET.get('type', ''))
        skip = int(request.GET.get('skip', 0))
        limit = int(request.GET.get('limit', 10))
        me = request.GET.get('me', False)
        if type == '':
            return JsonResponse({'Error': 'Invalid type'}, status=400)
        try:
            games = PongService.get_games(user, type, skip, limit, me)
            return JsonResponse(games, status=200, safe=False)
        except Exception as e:
            return JsonResponse({'Error': str(e)}, status=400)
        
    
    def post(self, request , user : User) -> JsonResponse:
        """
        Creates a game for the user and assigns them as participant
        @param request: HttpRequest
        @param user: User
        @return: JsonResponse with game schema
        """
        if request.body != b'':
            body = json.loads(request.body)
            game_id = body.get('game_id', None)
        else:
            game_id = None
        try :
            if game_id is not None:
                game = PongService.join_game(user, game_id)
            else:
                game = PongService.create_game(user)
            return JsonResponse(game, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
    def delete(self, request, user : User) -> JsonResponse:
        """
        Deletes the game for the user
        @param request: HttpRequest
        @param user: User
        @return: JsonResponse with game schema
        """
        if request.body == b'':
            return JsonResponse({'Error': 'Invalid request'}, status=400)
        data = json.loads(request.body)
        try:
            game_id = data.get('game_id', None)
            game = PongService.delete_game(game_id, user)
            return JsonResponse(game, status=200)
        except Exception as e:
            return JsonResponse({'Error': str(e)}, status=400)
        
@jwt_auth_required()
def get_game_by_id(request,user : User, game_id) -> JsonResponse:
    """
    Returns the game by id
    @param request: HttpRequest
    @param user: User
    @param game_id: int
    @return: JsonResponse with game schema
    """
    try:
        game = PongService.get_game_by_id(game_id)
        return JsonResponse(game, status=200)
    except Exception as e:
        return JsonResponse({'Error': str(e)}, status=400)