from gargantext import settings
from rest_framework_jwt.settings import api_settings
from calendar import timegm

from .dates import datetime

def jwt_payload_handler(user):
    username = user.username
    payload = {
        'user_id': user.pk,
        'role': settings.ROLE_ADMIN if username == settings.ROLE_ADMIN else \
                settings.ROLE_USER,
        'username': username,
        'exp': datetime.now() + api_settings.JWT_EXPIRATION_DELTA
    }

    # Include original issued at time for a brand new token,
    # to allow token refresh
    if api_settings.JWT_ALLOW_REFRESH:
        payload['orig_iat'] = timegm(
            datetime.utcnow().utctimetuple()
        )

    if api_settings.JWT_AUDIENCE is not None:
        payload['aud'] = api_settings.JWT_AUDIENCE

    if api_settings.JWT_ISSUER is not None:
        payload['iss'] = api_settings.JWT_ISSUER

    return payload

