"""
Сериализаторы для приложения пользователей
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .models import Role, UserRole, UserProfile

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Пользовательский сериализатор токена с дополнительной информацией о пользователе."""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Добавление пользовательских полей
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        # Добавление информации о пользователе в ответ
        data['user'] = UserSerializer(self.user).data
        return data


class RoleSerializer(serializers.ModelSerializer):
    """Сериализатор для модели роли."""
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']


class UserRoleSerializer(serializers.ModelSerializer):
    """Сериализатор для модели назначения роли пользователю."""
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), source='role', write_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'role', 'role_id', 'assigned_at']
        read_only_fields = ['assigned_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для модели профиля пользователя."""
    
    class Meta:
        model = UserProfile
        fields = ['id', 'phone', 'address', 'city', 'postal_code', 'country', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели пользователя."""
    profile = UserProfileSerializer(read_only=True)
    roles = UserRoleSerializer(source='user_roles', many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'is_active', 
            'date_joined', 'profile', 'roles'
        ]
        read_only_fields = ['date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания новых пользователей."""
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают'})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления профиля пользователя."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
