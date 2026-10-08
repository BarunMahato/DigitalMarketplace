from rest_framework import serializers

from .models import Course


class CourseSerializer(serializers.ModelSerializer):
    instructor = serializers.CharField(source="instructor.username", read_only=True)
    banner = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Course
        fields = (
            "id", "title", "description", "price", "status", "file", "banner",
            "instructor", "inventory", "created_at", "updated_at",
        )
        read_only_fields = ("id", "instructor", "created_at", "updated_at")

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_banner(self, value):
        if value and value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Banner image must be no larger than 2 MB.")
        return value
