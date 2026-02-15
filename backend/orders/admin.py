"""
настройка админки для приложения заказов
"""
from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import OrderStatus, Order, OrderItem
from simple_history.admin import SimpleHistoryAdmin


class OrderItemInline(admin.TabularInline):
    # inline для отображения товаров в заказе
    model = OrderItem
    extra = 0
    readonly_fields = (
        'get_product_name', 'product_sku', 'price', 
        'quantity', 'get_total_price_display', 'created_at'
    )
    raw_id_fields = ('product',)
    
    @display(description=_('товар'))
    def get_product_name(self, obj):
        # отображение названия товара со ссылкой
        from django.urls import reverse
        url = reverse('admin:products_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    
    @display(description=_('сумма'))
    def get_total_price_display(self, obj):
        # отображение общей стоимости позиции
        return f'{obj.get_total_price()} ₽'


@admin.register(OrderStatus)
class OrderStatusAdmin(SimpleHistoryAdmin):
    # настройка админки для модели статусов заказа
    list_display = ('name', 'description', 'is_final', 'created_at')
    list_filter = ('is_final', 'created_at')
    search_fields = ('name', 'description')
    list_per_page = 25
    list_display_links = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_final')
        }),
        (_('даты'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)


@admin.register(Order)
class OrderAdmin(SimpleHistoryAdmin):
    # настройка админки для модели заказа
    list_display = (
        'id', 'get_user_email', 'get_status_display',
        'get_total_display', 'get_items_count', 'created_at'
    )
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('user__email', 'shipping_address', 'notes', 'id')
    list_per_page = 25
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'status')
    filter_horizontal = ()
    list_display_links = ('id', 'get_user_email')
    
    inlines = (OrderItemInline,)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'status', 'total', 'shipping_address', 'notes')
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
    
    @display(description=_('статус'))
    def get_status_display(self, obj):
        # отображение статуса с цветовой индикацией
        if obj.status.is_final:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                obj.status.name
            )
        return format_html(
            '<span style="color: orange;">{}</span>',
            obj.status.name
        )
    
    @display(description=_('сумма'))
    def get_total_display(self, obj):
        # отображение общей суммы заказа
        return f'{obj.total} ₽'
    
    @display(description=_('количество товаров'))
    def get_items_count(self, obj):
        # получение количества товаров в заказе
        return obj.items.count()
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items', 'user')
    
    def save_model(self, request, obj, form, change):
        # сохранение заказа с пересчётом суммы
        if not change:
            pass
        super().save_model(request, obj, form, change)


@admin.register(OrderItem)
class OrderItemAdmin(SimpleHistoryAdmin):
    # настройка админки для модели товара в заказе
    list_display = (
        'get_order_id', 'get_product_name', 'product_sku',
        'price', 'quantity', 'get_total_price_display', 'created_at'
    )
    list_filter = ('created_at', 'price', 'product__categories')
    search_fields = ('product_name', 'product_sku', 'order__user__email', 'order__id')
    list_per_page = 25
    date_hierarchy = 'created_at'
    raw_id_fields = ('order', 'product')
    list_display_links = ('get_order_id', 'get_product_name')
    
    @display(description=_('заказ №'))
    def get_order_id(self, obj):
        # отображение номера заказа со ссылкой
        from django.urls import reverse
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">#{}</a>', url, obj.order.id)
    
    @display(description=_('товар'))
    def get_product_name(self, obj):
        # отображение названия товара со ссылкой
        if obj.product:
            from django.urls import reverse
            url = reverse('admin:products_product_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product_name)
        return obj.product_name
    
    @display(description=_('сумма'))
    def get_total_price_display(self, obj):
        # отображение общей стоимости позиции
        return f'{obj.get_total_price()} ₽'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__user', 'product')
