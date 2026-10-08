from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .tokens import InvalidToken, decode_token, encode_token, get_token_pair


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class TokenLoginView(APIView):
    """Exchange username/password for an access and refresh token pair."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None or not user.is_active:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(get_token_pair(user), status=status.HTTP_200_OK)


class TokenRefreshView(APIView):
    """Exchange a valid refresh token for a new access token."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh = request.data.get("refresh")
        if not isinstance(refresh, str):
            return Response({"detail": "A refresh token is required."}, status=400)
        try:
            claims = decode_token(refresh, "refresh")
        except InvalidToken:
            return Response({"detail": "Invalid or expired refresh token."}, status=401)

        try:
            user = get_user_model().objects.get(pk=claims["sub"], is_active=True)
        except (get_user_model().DoesNotExist, ValueError, TypeError):
            return Response({"detail": "Invalid or expired refresh token."}, status=401)

        # Refresh tokens are accepted only by this endpoint; issue a new access token.
        access = encode_token(user, "access", settings.JWT_ACCESS_EXPIRY_MINUTES * 60)
        return Response({"access": access}, status=status.HTTP_200_OK)
