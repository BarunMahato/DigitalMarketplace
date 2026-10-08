from typing import Generic

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import UserCreateSerializer


class CreateUserView(APIView):
    permission_classes = [AllowAny]
    role = User.Role.STUDENT

    def post(self, request):
        serializer = UserCreateSerializer(
            data=request.data, context={"role": self.role}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        avatar_url = user.profile.avatar.url if user.profile.avatar else None
        return Response(
            {
                "id": user.pk,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "bio": user.profile.bio,
                "avatar": avatar_url,
            },
            status=status.HTTP_201_CREATED,
        )


class CreateInstructorView(CreateUserView):
    role = User.Role.INSTRUCTOR
