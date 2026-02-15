"""
Custom permissions for role-based access control.
"""
from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAdminUser(permissions.BasePermission):
    """
    Permission check for admin role.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists()


class IsUser(permissions.BasePermission):
    """
    Permission check for regular user role.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_roles.filter(role__name='user').exists()


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Permission check for manager or admin role.
    Manager is defined by having manager_id assigned in supplier_product_requests.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Check if user is admin
        if request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists():
            return True
        # Check if user is manager of any request
        from suppliers.models import SupplierProductRequest
        return SupplierProductRequest.objects.filter(manager_id=request.user.id).exists()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners to edit their objects.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner or admin
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can do anything
        if request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists():
            return True
        
        # Check if user owns the object
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read for all, write only for admin.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists()


class IsManagerForRequest(permissions.BasePermission):
    """
    Permission check for manager of specific supplier product request.
    User is manager if they are assigned as manager_id in the request.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can do anything
        if request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists():
            return True
        
        # Check if user is manager of this request
        if hasattr(obj, 'manager_id'):
            return obj.manager_id == request.user.id
        
        return False


class CanManageSupplierRequests(permissions.BasePermission):
    """
    Permission to manage supplier product requests.
    Admin can manage all requests, manager can manage their assigned requests.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can do anything
        if request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists():
            return True
        
        # Check if user is manager of this request
        if hasattr(obj, 'manager_id'):
            return obj.manager_id == request.user.id
        
        return False


class CanAssignManager(permissions.BasePermission):
    """
    Permission to assign manager to supplier product request.
    Only admin can assign managers.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists()


class IsAuthenticatedOrReadOnlyForPublic(permissions.BasePermission):
    """
    Allows read access to everyone, write only to authenticated users.
    For public endpoints like categories and products.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
