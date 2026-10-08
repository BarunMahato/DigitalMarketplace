from django.contrib.auth import get_user_model, password_validation
from django.db import transaction
from rest_framework import serializers


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    bio = serializers.CharField(required=False, allow_blank=True, write_only=True)
    avatar = serializers.ImageField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            "id", "username", "email", "first_name", "last_name", "password",
            "bio", "avatar",
        )
        read_only_fields = ("id",)

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        role = self.context["role"]
        bio = validated_data.pop("bio", "")
        avatar = validated_data.pop("avatar", None)
        with transaction.atomic():
            user = get_user_model().objects.create_user(**validated_data, role=role)
            # The User post_save signal creates this profile for a new account.
            profile = user.profile
            profile.bio = bio
            if avatar is not None:
                profile.avatar = avatar
            profile.save(update_fields=("bio", "avatar"))
        return user
