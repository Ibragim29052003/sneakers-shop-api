"""
URL configuration for users app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    UserCreateAPIView,
    UserProfileView,
    UserViewSet,
    RoleViewSet,
    ManagersListView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')

urlpatterns = [
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', UserCreateAPIView.as_view(), name='user_register'),
    path('auth/profile/', UserProfileView.as_view(), name='user_profile'),
    path('managers/', ManagersListView.as_view(), name='managers-list'),
    path('', include(router.urls)),
]
