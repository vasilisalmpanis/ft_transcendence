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
        try:
            type = str(request.GET.get('type', ''))
            skip = int(request.GET.get('skip', 0))
            limit = int(request.GET.get('limit', 10))
            me = request.GET.get('me', False)
            if skip < 0 or limit < 0:
                return JsonResponse({'status': 'Invalid skip or limit'}, status=400)
            if type == '':
                return JsonResponse({'status': 'Invalid type'}, status=400)
            games = PongService.get_games(user, type, skip, limit, me)
            return JsonResponse(games, status=200, safe=False)
        except Exception as e:
            return JsonResponse({'status': str(e)}, status=400)
        
    
    def post(self, request , user : User) -> JsonResponse:
        """
        Creates a game for the user and assigns them as participant
        @param request: HttpRequest
        @param user: User
        @return: JsonResponse with game schema
        """
        try:
            max_points = int(request.GET.get('max_points', 10))
            if max_points < 1:
                return JsonResponse({'status': 'Invalid max_points'}, status=400)
            game = PongService.create_game(user, max_points)
            return JsonResponse(game, status=201)
        except Exception as e:
            return JsonResponse({'status': str(e)}, status=400)
        
    def delete(self, request, user : User) -> JsonResponse:
        """
        Deletes the game for the user
        @param request: HttpRequest
        @param user: User
        @return: JsonResponse with game schema
        """
        try:
            if request.body == b'':
                return JsonResponse({'status': 'Invalid request'}, status=400)
            data = json.loads(request.body)
            game_id = int(data.get('game_id'))
            if game_id < 1:
                return JsonResponse({'status': 'Invalid game_id'}, status=400)
            game = PongService.delete_game(game_id, user)
            return JsonResponse(game, status=200)
        except Exception as e:
            return JsonResponse({'status': str(e)}, status=400)
        
@jwt_auth_required()
def get_game_by_id(request,user : User, game_id: int) -> JsonResponse:
    """
    Returns the game by id
    @param request: HttpRequest
    @param user: User
    @param game_id: int
    @return: JsonResponse with game schema
    """
    try:
        if game_id < 1:
            return JsonResponse({'status': 'Invalid game_id'}, status=400)
        game = PongService.get_game_by_id(game_id)
        return JsonResponse(game, status=200)
    except Exception as e:
        return JsonResponse({'status': str(e)}, status=400)
    

@jwt_auth_required()
def get_user_games(request, user: User, id: int) -> JsonResponse:
    """
    Returns the games of the user
    @param request: HttpRequest
    @param user: User
    @param id: int
    @return: JsonResponse with game schema
    """
    try:
        type = str(request.GET.get('type', 'all'))
        skip = int(request.GET.get('skip', 0))
        limit = int(request.GET.get('limit', 10))
        if skip < 0 or limit < 0:
            return JsonResponse({'status': 'Invalid skip or limit'}, status=400)
        games = PongService.get_user_games(id, type, skip, limit, user)
        return JsonResponse(games, status=200, safe=False)
    except Exception as e:
        return JsonResponse({'status': str(e)}, status=400)