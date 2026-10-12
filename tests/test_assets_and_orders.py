import pytest
from django.contrib import admin
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.test import APIClient

from courses.admin import CourseAdmin, publish_selected_assets
from courses.models import Course


@pytest.mark.django_db
def test_unauthenticated_user_cannot_create_asset():
    response = APIClient().post(
        reverse("course-create"),
        {"title": "Unauthorized asset", "price": "10.00"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_non_instructor_cannot_publish_asset(student, instructor):
    draft_asset = Course.objects.create(
        title="Draft asset",
        price="10.00",
        status=Course.Status.DRAFT,
        instructor=instructor,
    )
    request = RequestFactory().post("/admin/courses/course/")
    request.user = student
    modeladmin = CourseAdmin(Course, admin.site)

    response = publish_selected_assets(
        modeladmin,
        request,
        Course.objects.filter(pk=draft_asset.pk),
    )

    assert response.status_code == 403
    draft_asset.refresh_from_db()
    assert draft_asset.status == Course.Status.DRAFT


@pytest.mark.django_db
def test_creating_order_decrements_inventory(
    monkeypatch, published_course, student_api_client
):
    monkeypatch.setattr(
        "orders.views.send_order_confirmation_email.delay",
        lambda order_id: None,
    )

    response = student_api_client.post(
        reverse("order-create"),
        {"course_id": published_course.pk, "quantity": 2},
        format="json",
    )

    assert response.status_code == 201
    published_course.refresh_from_db()
    assert published_course.inventory == 3
