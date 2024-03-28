from users.models                       import User
from tournament.models                  import Tournament, tournament_model_to_dict
from transcendence_backend.decorators   import validate_jwt
from asgiref.sync                       import sync_to_async 
from django.http                        import JsonResponse
from channels.db						import database_sync_to_async
from jwt                                import JWT
from django.conf                        import settings
import logging
from django.db.models import Q

logger = logging.getLogger(__name__)

def get_tournament_id(user: User):
    tournament = Tournament.objects.filter(players=user).filter(Q(status='open') | Q(status='locked'))
    if tournament.exists():
        return tournament.first()
    return None

class AuthMiddleware:
    """
    Custom middleware (insecure) that takes user IDs from the query string.
    """

    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):
        # Look up user from query string (you should also do things like
        # checking if it is a valid user ID, or if scope["user"] is already
        # populated).
        headers = dict(scope["headers"])
        headers_dict = {
            item[0].decode('utf-8'): item[1].decode('utf-8')
            for item in scope["headers"]
        }
        authorization = headers_dict.get("authorization", "").split(" ")[-1]
        authorization = authorization.strip("$")
        logger.info(f"Authorization: {authorization}")

        

        if authorization:
            try:
                jwt = JWT(settings.JWT_SECRET)
                payload = await sync_to_async(jwt.decrypt_jwt)(authorization)
                scope["user"] = await sync_to_async(validate_jwt)(payload, second_factor=False, days=1)

                # Bounces the user if the path is tournament and the user is has yet joined
                if scope["path"] == "/tournament":
                    tournament = await database_sync_to_async(get_tournament_id)(scope["user"])
                    if tournament:
                        scope["tournament"] = tournament
                    else:
                        return JsonResponse({'error': 'User not in a tournament'}, status=400)
                    

            except Exception as e:
                scope["user"] = None
                logger.warn(f"Error: {e}")
                return JsonResponse({'error': 'Authorization header required'}, status=401)
        else:
            return JsonResponse({'error': 'Authorization header required'}, status=401)


        return await self.app(scope, receive, send)