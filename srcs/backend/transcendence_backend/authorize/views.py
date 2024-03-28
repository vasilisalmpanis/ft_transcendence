from venv import logger
from django.shortcuts                   import render
from users.models                       import User
from users.services                     import UserService, SecondFactorService
from transcendence_backend.decorators   import jwt_auth_required
from django.http                        import JsonResponse
from jwt                                import JWT
from django.conf                        import settings
from datetime                           import datetime, timedelta
from time                               import strftime
from django.contrib.auth                import authenticate
import json
import logging

logger = logging.getLogger(__name__)

# Create your views here.

def create_token(jwt : JWT, user : User, expiration : datetime, isa : datetime | None, second_factor : bool = False) -> str:
    """
    Creates a token for the user
    :param jwt: JWT object
    :param user: User object
    :param expiration: Expiration date
    :param isa: Issued at date
    """
    if isa == None:
        isa = datetime.now()
    return jwt.create_jwt({"sub": user.id,
                           "exp": strftime("%Y-%m-%d %H:%M:%S",expiration.timetuple()),
                           "iss" : "ft_transcendence",
                           "isa" : strftime("%Y-%m-%d %H:%M:%S",isa.timetuple()),
                            "is_authenticated" : (not second_factor)
                            }
                           )

def login_user(request) -> JsonResponse:
    """
    Authenticates the user
    :param request: Request object
    :return: JsonResponse
    """
    if request.method == "GET":
        return JsonResponse({"Login": "Wrong Request Method"}, status=200)
    data = json.loads(request.body)
    username = data.get("username", None)
    password = data.get("password", None)
    if username == None or password == None:
        return JsonResponse({"status": "Username or Password were not given"}, status=400)
    user = authenticate(username=username, password=password)
    #user = User.objects.get(username=username)
    if user != None:
        jwt = JWT(settings.JWT_SECRET)
        user.is_user_active = True
        UserService.update_last_login(user)
        access_token = create_token(jwt=jwt, 
                                    user=user, 
                                    expiration=datetime.now() + timedelta(days=1), 
                                    isa=user.last_login, second_factor=user.is_2fa_enabled)
        refresh_token = create_token(jwt=jwt,
                                     user=user,
                                     expiration=datetime.now() + timedelta(days=30),
                                     isa=user.last_login,
                                     second_factor=user.is_2fa_enabled)
        return JsonResponse({
                                "access_token": access_token,
                                "refresh_token" : refresh_token }, status=200
                            )
    else:
        return JsonResponse({"status": "error"}, status=401)

@jwt_auth_required()
def logout_user(request, user : User) -> JsonResponse:
    """
    Logs out the user
    :param request: Request object
    :param user: User object
    :return: JsonResponse
    """
    if request.method != 'POST':
        return JsonResponse({"status": "Wrong Request Method"}, status=400)
    user.is_user_active = False
    user.save()
    return JsonResponse({"status": "Logged Out"}, status=200)

@jwt_auth_required(days=30)
def refresh_token(request, user : User) -> JsonResponse:
    """
    Refreshed the access token for the currently authorized user
    :param request: Request object
    :param user: User object
    :return: JsonResponse
    """
    if request.method != 'GET':
        return JsonResponse({"status": "Wrong Request Method"}, status=400)
    jwt = JWT(settings.JWT_SECRET)
    UserService.update_last_login(user)
    access_token = create_token(jwt=jwt, user=user, expiration=datetime.now() + timedelta(days=1), isa=user.last_login)
    return JsonResponse({"access_token": access_token}, status=200)

@jwt_auth_required(second_factor=True)
def verify_2fa(request, user : User) -> JsonResponse:
    """
    Verifies the 2fa code for the user
    :param request: Request object
    :param user: User object
    :return: JsonResponse
    """
    if request.method != 'POST':
        return JsonResponse({"status": "Wrong Request Method"}, status=400)
    data = json.loads(request.body)
    code = str(data.get("2fa_code", None))
    if code == None:
        return JsonResponse({"Error": "No code in request body"}, status=400)
    if user.is_2fa_enabled == False:
        return JsonResponse({"Error": "2FA is not enabled"}, status=400)
    if SecondFactorService.verify_2fa(user, code):
        jwt = JWT(settings.JWT_SECRET)
        UserService.update_last_login(user)
        access_token = create_token(jwt=jwt, user=user, expiration=datetime.now() + timedelta(days=1), isa=user.last_login, second_factor=False)
        refresh_token = create_token(jwt=jwt, user=user, expiration=datetime.now() + timedelta(days=30), isa=user.last_login, second_factor=False)
        return JsonResponse({"access_token": access_token, "refresh_token" : refresh_token}, status=200)
    else:
        return JsonResponse({"status": "incorrect code"}, status=401)
    