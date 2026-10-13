"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from accounts.views import CreateInstructorView, CreateUserView
from accounts.token_views import TokenLoginView, TokenRefreshView
from courses.views import CourseCreateView, CourseDetailView, CourseListView
from orders.views import OrderCreateView, OrderDetailView, OrderListView, RevenueReportView
from config.views import APIRootView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', APIRootView.as_view(), name='api-root'),
    path('api/createUser', CreateUserView.as_view(), name='create-user'),
    path('api/createInstructor', CreateInstructorView.as_view(), name='create-instructor'),
    path('api/register', TokenLoginView.as_view(), name='token-login'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/getcourses/', CourseListView.as_view(), name='course-list'),
    path('api/getCourse/<int:course_id>/', CourseDetailView.as_view(), name='course-detail'),
    path('api/createCourse', CourseCreateView.as_view(), name='course-create'),
    path('api/orders/', OrderListView.as_view(), name='order-list'),
    path('api/createOrder/', OrderCreateView.as_view(), name='order-create'),
    path('api/order/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('api/getRevenue/', RevenueReportView.as_view(), name='revenue-report'),
    path('silk', include('silk.urls', namespace='silk')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
