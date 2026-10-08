from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("course", "course_title", "unit_price", "quantity")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    student = serializers.CharField(source="student.username", read_only=True)

    class Meta:
        model = Order
        fields = ("id", "student", "status", "total_amount", "created_at", "items")
