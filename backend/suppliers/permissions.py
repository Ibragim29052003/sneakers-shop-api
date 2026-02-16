"""
Кастомные разрешения для ролевой модели доступа.
"""
from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAdminUser(permissions.BasePermission):
    """
    Проверка разрешений для администратора.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists()


class IsUser(permissions.BasePermission):
    """
    Проверка разрешений для обычного пользователя.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_roles.filter(role__name='user').exists()


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Проверка разрешений для менеджера или администратора.
    Менеджер определяется по назначению manager_id в заявках поставщиков.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Проверка, является ли пользователь админом
        if request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists():
            return True
        # Проверка, является ли пользователь менеджером какой-либо заявки
        from suppliers.models import SupplierProductRequest
        return SupplierProductRequest.objects.filter(manager_id=request.user.id).exists()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение уровня объекта, позволяющее только владельцам редактировать свои объекты.
    """
    def has_object_permission(self, request, view, obj):
        # Разрешения на чтение разрешены для любого запроса
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Разрешения на запись только для владельца или админа
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Админ может делать все
        if request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists():
            return True
        
        # Проверка, является ли пользователь владельцем объекта
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешить чтение всем, запись только админу.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists()


class IsManagerForRequest(permissions.BasePermission):
    """
    Проверка разрешений для менеджера конкретной заявки поставщика.
    Пользователь является менеджером, если ему назначен manager_id в заявке.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Админ может делать все
        if request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists():
            return True
        
        # Проверка, является ли пользователь менеджером этой заявки
        if hasattr(obj, 'manager_id'):
            return obj.manager_id == request.user.id
        
        return False


class CanManageSupplierRequests(permissions.BasePermission):
    """
    Проверка разрешений для управления заявками поставщиков.
    Админ может управлять всеми заявками, менеджер может управлять назначенными ему заявками.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Админ может делать все
        if request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists():
            return True
        
        # Проверка, является ли пользователь менеджером этой заявки
        if hasattr(obj, 'manager_id'):
            return obj.manager_id == request.user.id
        
        return False


class CanAssignManager(permissions.BasePermission):
    """
    Проверка разрешений для назначения менеджера заявке поставщика.
    Только админ может назначать менеджеров.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists()


class IsAuthenticatedOrReadOnlyForPublic(permissions.BasePermission):
    """
    Разрешает доступ на чтение всем, на запись только аутентифицированным пользователям.
    Для публичных эндпоинтов, таких как категории и товары.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
