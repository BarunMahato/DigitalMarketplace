from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class APIRootView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        routes = {
            "create_student": ("POST", "/api/createUser"),
            "create_instructor": ("POST", "/api/createInstructor"),
            "login_and_get_tokens": ("POST", "/api/register"),
            "refresh_access_token": ("POST", "/api/token/refresh"),
            "courses": ("GET", "/api/getcourses/"),
            "course_detail": ("GET", "/api/getCourse/{id}/"),
            "create_course": ("POST", "/api/createCourse"),
            "orders": ("GET", "/api/orders"),
            "create_order": ("POST", "/api/createOrder"),
            "order_detail": ("GET", "/api/order/{id}"),
            "sales_revenue_report": ("GET", "/api/getRevenue"),
        }
        return Response({
            name: {
                "method": method,
                "url": request.build_absolute_uri(path),
            }
            for name, (method, path) in routes.items()
        })
