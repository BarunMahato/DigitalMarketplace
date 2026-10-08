from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header

from .tokens import InvalidToken, decode_token


class CustomJWTAuthentication(BaseAuthentication):
    """Authenticate requests carrying ``Authorization: Bearer <access-token>``."""

    keyword = b"bearer"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if parts[0].lower() != self.keyword:
            return None
        if len(parts) != 2:
            raise exceptions.AuthenticationFailed("Invalid Authorization header")

        try:
            token = parts[1].decode("ascii")
            claims = decode_token(token, "access")
            user = get_user_model().objects.get(pk=claims["sub"])
        except (UnicodeDecodeError, InvalidToken, get_user_model().DoesNotExist,
                ValueError, TypeError):
            raise exceptions.AuthenticationFailed("Invalid or expired access token")

        if not user.is_active:
            raise exceptions.AuthenticationFailed("User account is inactive")
        return user, claims

    def authenticate_header(self, request):
        return "Bearer"
