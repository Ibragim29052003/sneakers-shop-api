"""
настройка админки для приложения отзывов
"""
from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Review
from simple_history.admin import SimpleHistoryAdmin


@admin.register(Review)
class ReviewAdmin(SimpleHistoryAdmin):
    # настройка админки для модели отзыва
    list_display = (
        'get_user_email', 'get_product_name', 'get_rating_stars',
        'get_moderation_status', 'is_verified_purchase', 'created_at'
    )
    list_filter = (
        'rating', 'is_moderated', 'is_verified_purchase',
        'created_at', 'product__categories'
    )
    search_fields = (
        'user__email', 'product__name', 'comment'
    )
    list_per_page = 25
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'product')
    list_display_links = ('get_user_email', 'get_product_name')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'product', 'rating', 'comment')
        }),
        (_('статус'), {
            'fields': ('is_moderated', 'is_verified_purchase')
        }),
        (_('даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    @display(description=_('пользователь'))
    def get_user_email(self, obj):
        # отображение email пользователя со ссылкой
        from django.urls import reverse
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    
    @display(description=_('товар'))
    def get_product_name(self, obj):
        # отображение названия товара со ссылкой
        from django.urls import reverse
        url = reverse('admin:products_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    
    @display(description=_('оценка'))
    def get_rating_stars(self, obj):
        # отображение оценки в виде звёзд
        return format_html(
            '<span style="color: gold; font-size: 16px;">{}</span>',
            '★' * obj.rating
        )
    
    @display(description=_('статус'))
    def get_moderation_status(self, obj):
        # отображение статуса модерации
        if obj.is_moderated:
            return format_html('<span style="color: green;">✓ промодерирован</span>')
        return format_html('<span style="color: orange;">⏳ на модерации</span>')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product')
    
    actions = ['approve_reviews', 'reject_reviews']
    
    @admin.action(description='одобрить выбранные отзывы')
    def approve_reviews(self, request, queryset):
        # одобрение выбранных отзывов
        updated = queryset.update(is_moderated=True)
        self.message_user(request, f'{updated} отзывов одобрено.')
    
    @admin.action(description='отклонить выбранные отзывы')
    def reject_reviews(self, request, queryset):
        # отклонение выбранных отзывов
        updated = queryset.update(is_moderated=False)
        self.message_user(request, f'{updated} отзывов отклонено.')
