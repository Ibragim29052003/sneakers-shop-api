from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    """Разрешает доступ только staff/admin роли."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or user.user_roles.filter(role__name='admin').exists()


class IsAdminOrReadOnly(permissions.BasePermission):
    """Чтение доступно всем, изменение — только админу."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or user.user_roles.filter(role__name='admin').exists()


class IsOwnerOrAdmin(permissions.BasePermission):
    """Доступ владельцу объекта или админу."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.user_roles.filter(role__name='admin').exists():
            return True
        owner = getattr(obj, 'user', None)
        return owner == user


class IsOrderOwnerOrAdmin(permissions.BasePermission):
    """Для заказов: доступ владельцу или админу."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.user_roles.filter(role__name='admin').exists():
            return True
        return obj.user == user
