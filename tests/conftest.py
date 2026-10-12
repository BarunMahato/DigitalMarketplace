from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from courses.models import Course


@pytest.fixture
def student(db, django_user_model):
    return django_user_model.objects.create_user(
        username="student",
        email="student@example.com",
        password="test-password",
        role="STUDENT",
    )


@pytest.fixture
def instructor(db, django_user_model):
    return django_user_model.objects.create_user(
        username="instructor",
        email="instructor@example.com",
        password="test-password",
        role="INSTRUCTOR",
    )


@pytest.fixture
def student_api_client(student):
    client = APIClient()
    client.force_authenticate(user=student)
    return client


@pytest.fixture
def published_course(db, instructor):
    return Course.objects.create(
        title="Test asset",
        description="An asset for order tests.",
        price=Decimal("12.50"),
        status=Course.Status.PUBLISHED,
        instructor=instructor,
        inventory=5,
    )
