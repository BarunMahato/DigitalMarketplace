from django.contrib import admin, messages
from django.http import HttpResponseForbidden

from .models import Course


@admin.action(description="Publish selected assets")
def publish_selected_assets(modeladmin, request, queryset):
    if getattr(request.user, "role", None) != "INSTRUCTOR":
        return HttpResponseForbidden("Instructor accounts only.")

    updated = queryset.exclude(status=Course.Status.PUBLISHED).update(
        status=Course.Status.PUBLISHED
    )
    modeladmin.message_user(
        request,
        f"{updated} asset(s) published.",
        messages.SUCCESS,
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "price", "status", "created_at")
    list_filter = ("status", "created_at", "price")
    search_fields = ("title", "description", "instructor__username")
    actions = (publish_selected_assets,)
