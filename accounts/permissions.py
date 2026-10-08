from rest_framework.permissions import BasePermission


class IsInstructor(BasePermission):
    message = "Instructor accounts only."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "INSTRUCTOR")


class IsStudent(BasePermission):
    message = "Student accounts only."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "STUDENT")
