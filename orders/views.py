from decimal import Decimal

from django.db import transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsInstructor, IsStudent
from courses.models import Course
from .models import Order, OrderItem
from .serializers import OrderSerializer


class OrderListView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        orders = (
            Order.objects.filter(student=request.user)
            .select_related("student")
            .prefetch_related("items__course")
        )
        return Response(OrderSerializer(orders, many=True).data)


class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request):
        course_id = request.data.get("course_id")
        quantity = request.data.get("quantity", 1)
        try:
            course_id = int(course_id)
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response(
                {"detail": "course_id and a positive integer quantity are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if quantity < 1:
            return Response({"detail": "Quantity must be at least 1."}, status=400)

        with transaction.atomic():
            course = Course.objects.select_for_update().filter(
                pk=course_id, status=Course.Status.PUBLISHED
            ).first()
            if course is None:
                return Response({"detail": "Published course not found."}, status=404)

            # The conditional update and F expression keep stock decrements atomic.
            updated = Course.objects.filter(pk=course.pk, inventory__gte=quantity).update(
                inventory=F("inventory") - quantity
            )
            if not updated:
                return Response({"detail": "Insufficient course inventory."}, status=409)

            total = course.price * quantity
            order = Order.objects.create(
                student=request.user,
                status=Order.Status.COMPLETED,
                total_amount=total,
            )
            OrderItem.objects.create(
                order=order,
                course=course,
                unit_price=course.price,
                quantity=quantity,
            )

        order = Order.objects.select_related("student").prefetch_related("items__course").get(pk=order.pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, order_id):
        order = (
            Order.objects.filter(pk=order_id, student=request.user)
            .select_related("student")
            .prefetch_related("items__course")
            .first()
        )
        if order is None:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)


class RevenueReportView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request):
        revenue_expression = ExpressionWrapper(
            F("order_items__unit_price") * F("order_items__quantity"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        completed = Q(order_items__order__status=Order.Status.COMPLETED)
        courses = (
            Course.objects.filter(instructor=request.user)
            .annotate(
                purchase_count=Count("order_items__order", filter=completed, distinct=True),
                revenue=Sum(revenue_expression, filter=completed),
            )
            .order_by("id")
        )
        totals = OrderItem.objects.filter(
            course__instructor=request.user,
            order__status=Order.Status.COMPLETED,
        ).aggregate(
            total_revenue=Sum(
                ExpressionWrapper(
                    F("unit_price") * F("quantity"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ),
            total_purchases=Count("order_id", distinct=True),
        )
        return Response({
            "total_revenue": str(totals["total_revenue"] or Decimal("0.00")),
            "total_purchases": totals["total_purchases"],
            "courses": [
                {
                    "id": course.pk,
                    "title": course.title,
                    "purchase_count": course.purchase_count,
                    "revenue": str(course.revenue or Decimal("0.00")),
                }
                for course in courses
            ],
        })
