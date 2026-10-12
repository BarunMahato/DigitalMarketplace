from rest_framework import filters, status
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.views import APIView

from accounts.permissions import IsInstructor
from .models import Course
from .filters import CourseFilterBackend
from .pagination import CoursePageNumberPagination
from .serializers import CourseSerializer


class CourseListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer
    pagination_class = CoursePageNumberPagination
    filter_backends = [
        CourseFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["title"]
    ordering_fields = ["price", "created_at"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        request = self.request
        courses = Course.objects.select_related("instructor")
        if request.user.role == "INSTRUCTOR":
            courses = courses.filter(instructor=request.user)
        else:
            courses = courses.published()
        return courses

    @method_decorator(cache_page(60))
    @method_decorator(vary_on_headers("Authorization"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CourseDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        courses = Course.objects.select_related("instructor")
        if request.user.role == "INSTRUCTOR":
            courses = courses.filter(instructor=request.user)
        else:
            courses = courses.published()
        course = courses.filter(pk=course_id).first()
        if course is None:
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(CourseSerializer(course, context={"request": request}).data)


class CourseCreateView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsInstructor]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = CourseSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.save(instructor=request.user)
        return Response(self.get_serializer(course).data, status=status.HTTP_201_CREATED)
