from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView

from accounts.permissions import IsInstructor
from .models import Course
from .serializers import CourseSerializer


class CourseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        courses = Course.objects.select_related("instructor")
        if request.user.role == "INSTRUCTOR":
            courses = courses.filter(instructor=request.user)
        else:
            courses = courses.published()
        return Response(CourseSerializer(courses, many=True, context={"request": request}).data)


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
