"""
Views for users app.
"""
from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .models import Role, UserRole, UserProfile
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserProfileSerializer,
    RoleSerializer,
    UserRoleSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token view with user info."""
    serializer_class = CustomTokenObtainPairSerializer


class UserCreateAPIView(generics.CreateAPIView):
    """API view for user registration."""
    serializer_class = UserCreateSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Create empty profile for new user
        UserProfile.objects.create(user=user)
        # Assign default 'user' role
        try:
            default_role = Role.objects.get(name='user')
            UserRole.objects.create(user=user, role=default_role)
        except Role.DoesNotExist:
            pass
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """API view for user profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user.profile
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User management."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'list']:
            return []
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)


class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet for Role management."""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]


class UserRoleViewSet(viewsets.ModelViewSet):
    """ViewSet for UserRole management."""
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    
    def get_queryset(self):
        return super().get_queryset().filter(user_id=self.kwargs.get('user_pk'))
