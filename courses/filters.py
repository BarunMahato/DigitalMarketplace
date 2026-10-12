from rest_framework.filters import BaseFilterBackend


class CourseFilterBackend(BaseFilterBackend):
    """Allow exact filters for explicitly supported Course fields."""

    filter_fields = ("status", "price", "instructor")

    def filter_queryset(self, request, queryset, view):
        filters = {
            field: request.query_params[field]
            for field in self.filter_fields
            if request.query_params.get(field)
        }
        return queryset.filter(**filters)
