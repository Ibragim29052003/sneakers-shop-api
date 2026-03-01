"""
Представления для приложения пользователей
"""
from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
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
    """Пользовательское представление получения токена с информацией о пользователе."""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = []  # Разрешаем публичный вход


class UserCreateAPIView(generics.CreateAPIView):
    """API представление для регистрации пользователя."""
    serializer_class = UserCreateSerializer
    permission_classes = []  # Разрешаем публичную регистрацию
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Создание пустого профиля для нового пользователя
        UserProfile.objects.create(user=user)
        # Назначение роли по умолчанию
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
    """API представление для профиля пользователя."""
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
    """ViewSet для управления пользователями."""
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
    """ViewSet для управления ролями."""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]


class UserRoleViewSet(viewsets.ModelViewSet):
    """ViewSet для управления назначениями ролей."""
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    
    def get_queryset(self):
        return super().get_queryset().filter(user_id=self.kwargs.get('user_pk'))


class ManagersListView(APIView):
    """API view для получения списка менеджеров."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Получение всех пользователей с ролью менеджера или админа."""
        from .models import Role
        
        # Получаем роли менеджера и админа
        try:
            manager_role = Role.objects.get(name='manager')
            admin_role = Role.objects.get(name='admin')
            
            # Получаем пользователей с этими ролями
            manager_user_ids = UserRole.objects.filter(
                role__in=[manager_role, admin_role]
            ).values_list('user_id', flat=True)
            
            managers = User.objects.filter(id__in=manager_user_ids).select_related('profile')
            
            # Сериализуем данные
            result = []
            for manager in managers:
                result.append({
                    'id': manager.id,
                    'email': manager.email,
                    'first_name': manager.first_name,
                    'last_name': manager.last_name,
                    'is_active': manager.is_active,
                })
            
            return Response(result)
        except Role.DoesNotExist:
            return Response([])
