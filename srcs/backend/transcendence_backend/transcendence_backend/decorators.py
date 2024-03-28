# decorators.py
from functools      import wraps
from typing         import Any, Dict
from venv           import logger
from django.http    import JsonResponse
from jwt            import JWT
from django.conf    import settings
from users.models   import User
from datetime       import datetime, timedelta
from django.views   import View

import logging
logger = logging.getLogger(__name__)

def validate_jwt(payload : Dict, second_factor : bool, **kwargs) -> User:
    """
    Validates JWT payload
    :param payload: JWT payload
    :param kwargs: Additional arguments for expiration time
    :return: User object
    """
    iss = payload.get('iss', None)
    if iss != 'ft_transcendence':
        raise Exception("Invalid Issuer")
    user_id = payload.get('sub', None)
    if user_id is None:
        raise Exception("Invalid User_id")
    user = User.objects.get(id=user_id)
    if user is None:
        raise Exception("Invalid User")    
    isa = payload.get('isa', None)
    expiration = payload.get('exp', None)
    if expiration is None:
        raise Exception("Invalid Token")
    expiration = datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S')
    if expiration < datetime.now() or expiration > datetime.now() + timedelta(**kwargs):
        raise Exception("Token Expired")
    if isa is None:
        raise Exception("Invalid Token")
    isa = datetime.strptime(isa, '%Y-%m-%d %H:%M:%S')
    logger.warning(f"User: {user.username} Last Login: {user.last_login} ISA: {isa}")
    user_last_login = datetime.strptime(user.last_login.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')
    if isa < user_last_login or user.is_user_active != True:
        raise Exception("User not active")
    if second_factor:
        return user
    if user.is_2fa_enabled:
        if not payload.get("is_authenticated", False):
            raise Exception("2FA Required")
    return user

def jwt_auth_required(second_factor : bool = False, days : int = 1):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(*args, **kwargs):
            if isinstance(args[0], View):
                request = args[1]
            else:
                request = args[0]
            token = request.headers.get('Authorization')
            if token is None:
                return JsonResponse({'Error': 'Authorization header required'}, status=401)
            try:
                tokens = token.split(' ')
                for t in tokens[1:]:
                    if t != "":
                        token = t
            except IndexError:
                return JsonResponse({'Error': 'Access Token Required'}, status=401)
            jwt = JWT(settings.JWT_SECRET)
            try:
                payload = jwt.decrypt_jwt(token)
                user = validate_jwt(payload, second_factor=second_factor, days=days)
                kwargs['user'] = user
                return view_func(*args, **kwargs)
            except Exception as e:
                return JsonResponse({'Error': f"{str(e)}"}, status=401)
        return _wrapped_view
    return decorator

