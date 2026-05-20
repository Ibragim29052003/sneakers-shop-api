"""
настройка админки для приложения пользователей
"""
from typing import Any

from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import Role, UserRole, UserProfile
from simple_history.admin import SimpleHistoryAdmin

User = get_user_model()


class UserRoleInline(admin.TabularInline):
    # inline для отображения ролей пользователя
    model = UserRole
    extra = 0
    readonly_fields = ('assigned_at',)


class UserProfileInline(admin.StackedInline):
    # inline для отображения профиля пользователя
    model = UserProfile
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


@admin.register(User)
class UserAdmin(BaseUserAdmin, SimpleHistoryAdmin):
    # настройка админки для модели пользователя
    list_display = ('email', 'get_full_name', 'get_is_active_status', 'date_joined', 'last_login', 'get_role_names')
    list_filter = ('is_active', 'is_staff', 'date_joined', 'user_roles__role')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    date_hierarchy = 'date_joined'
    list_display_links = ('email', 'get_full_name')
    
    readonly_fields = ('date_joined', 'last_login')
    
    # убрали user_roles из filter_horizontal так как это ForeignKey, а не ManyToMany на прямую
    filter_horizontal = ()
    
    inlines = (UserProfileInline, UserRoleInline)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('персональная информация'), {'fields': ('first_name', 'last_name')}),
        (_('права доступа'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')
        }),
        (_('важные даты'), {'fields': ('date_joined', 'last_login')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    
    @display(description=_('фио'))
    def get_full_name(self, obj: Any) -> Any:
        # отображение полного имени пользователя
        """Возвращает данные через `get_full_name`."""
        return f'{obj.first_name} {obj.last_name}'
    
    @display(description=_('активен'))
    def get_is_active_status(self, obj: Any) -> Any:
        # отображение статуса активности с цветовой индикацией
        """Возвращает данные через `get_is_active_status`."""
        if obj.is_active:
            return format_html('<span style="color: green;">{} да</span>', '✓')
        return format_html('<span style="color: red;">{} нет</span>', '✗')
    
    @display(description=_('роли'))
    def get_role_names(self, obj: Any) -> Any:
        # отображение ролей пользователя
        """Возвращает данные через `get_role_names`."""
        roles = [ur.role.name for ur in obj.user_roles.select_related('role').all()]
        if roles:
            return ', '.join(roles)
        return '-'
    
    def get_queryset(self, request: Any) -> Any:
        """Возвращает данные через `get_queryset`."""
        return super().get_queryset(request).prefetch_related('user_roles', 'profile')
    
    def get_inline_instances(self, request: Any, obj: Any=None) -> Any:
        """Возвращает данные через `get_inline_instances`."""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(Role)
class RoleAdmin(SimpleHistoryAdmin):
    # настройка админки для модели ролей
    list_display = ('name', 'description', 'get_user_count')
    list_filter = ('name',)
    search_fields = ('name', 'description')
    
    @display(description=_('количество пользователей'))
    def get_user_count(self, obj: Any) -> Any:
        # отображение количества пользователей с данной ролью
        """Возвращает данные через `get_user_count`."""
        return obj.role_users.count()
    
    def get_queryset(self, request: Any) -> Any:
        """Возвращает данные через `get_queryset`."""
        return super().get_queryset(request).prefetch_related('role_users')


@admin.register(UserRole)
class UserRoleAdmin(SimpleHistoryAdmin):
    # настройка админки для модели назначения ролей
    list_display = ('get_user_email', 'get_role_name', 'assigned_at')
    list_filter = ('role', 'assigned_at')
    search_fields = ('user__email', 'role__name')
    date_hierarchy = 'assigned_at'
    raw_id_fields = ('user',)
    list_display_links = ('get_user_email', 'get_role_name')
    
    @display(description=_('пользователь'))
    def get_user_email(self, obj: Any) -> Any:
        # отображение email пользователя со ссылкой
        """Возвращает данные через `get_user_email`."""
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    
    @display(description=_('роль'))
    def get_role_name(self, obj: Any) -> Any:
        # отображение названия роли
        """Возвращает данные через `get_role_name`."""
        return obj.role.name


@admin.register(UserProfile)
class UserProfileAdmin(SimpleHistoryAdmin):
    # настройка админки для модели профиля пользователя
    list_display = ('get_user_email', 'phone', 'city', 'country', 'created_at')
    list_filter = ('city', 'country', 'created_at')
    search_fields = ('user__email', 'phone', 'address', 'city')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user',)
    list_display_links = ('get_user_email',)
    
    @display(description=_('пользователь'))
    def get_user_email(self, obj: Any) -> Any:
        # отображение email пользователя со ссылкой
        """Возвращает данные через `get_user_email`."""
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    
    def get_queryset(self, request: Any) -> Any:
        """Возвращает данные через `get_queryset`."""
        return super().get_queryset(request).select_related('user')
