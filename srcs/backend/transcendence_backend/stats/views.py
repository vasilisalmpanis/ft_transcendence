from django.shortcuts                   import render
from django.http                        import JsonResponse
from .models                            import Stats
from .services                          import StatService
from users.models                       import User
from users.services                     import UserService
from django.views                       import View
from transcendence_backend.decorators   import jwt_auth_required



## TODO Do we display blocked users or users who blocked us int the leaderboard?
@jwt_auth_required()
def getStatistics(request, user : User, id : int) -> JsonResponse:
    """
    Get statistics for a user by id
    """
    if request.method == "GET":
        try:
            new_user = User.objects.get(id=id)
            stats = StatService.get_stats(new_user)
            return JsonResponse(stats, status=200, safe=False)
        except Exception:
            return JsonResponse({"error": "user not found"}, status=400)
    return JsonResponse({"error": "wrong request method"}, status=400)

@jwt_auth_required()
def leaderBoard(request, user : User) -> JsonResponse:
    """
    Get all users statistics with pagination
    skip : int
    limit : int
    """
    if request.method == 'GET':
        try:        
            skip = int(request.GET.get("skip", 0))
            limit = int(request.GET.get("limit", 10))
            order = request.GET.get("order", "desc")
            stats = StatService.leaderboard(skip, limit, order)
            return JsonResponse(stats, status=200, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "wrong request method"}, status=400)