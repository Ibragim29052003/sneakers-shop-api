"""
настройка админки для приложения корзины
"""
from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Cart, CartItem
from simple_history.admin import SimpleHistoryAdmin


class CartItemInline(admin.TabularInline):
    # inline для отображения товаров в корзине
    model = CartItem
    extra = 0
    readonly_fields = (
        'get_product_name', 'get_product_price', 'get_total_price_display', 
        'created_at', 'updated_at'
    )
    raw_id_fields = ('product',)
    
    @display(description=_('товар'))
    def get_product_name(self, obj):
        # отображение названия товара со ссылкой
        from django.urls import reverse
        url = reverse('admin:products_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    
    @display(description=_('цена за шт.'))
    def get_product_price(self, obj):
        # отображение цены за единицу товара
        return f'{obj.product.price} ₽'
    
    @display(description=_('сумма'))
    def get_total_price_display(self, obj):
        # отображение общей стоимости позиции
        return f'{obj.get_total_price()} ₽'


@admin.register(Cart)
class CartAdmin(SimpleHistoryAdmin):
    # настройка админки для модели корзины
    list_display = ('get_user_email', 'get_total_items', 'get_total_price_display', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    raw_id_fields = ('user',)
    list_display_links = ('get_user_email',)
    
    inlines = (CartItemInline,)
    
    readonly_fields = ('created_at', 'updated_at')
    
    @display(description=_('пользователь'))
    def get_user_email(self, obj):
        # отображение email пользователя со ссылкой
        from django.urls import reverse
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    
    @display(description=_('количество товаров'))
    def get_total_items(self, obj):
        # получение общего количества товаров в корзине
        return obj.items.count()
    
    @display(description=_('общая сумма'))
    def get_total_price_display(self, obj):
        # отображение общей суммы с валютой
        return f'{obj.get_total_price()} ₽'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items', 'user')


@admin.register(CartItem)
class CartItemAdmin(SimpleHistoryAdmin):
    # настройка админки для модели товара в корзине
    list_display = (
        'get_cart_user', 'get_product_name', 'quantity',
        'get_product_price', 'get_total_price_display', 'created_at'
    )
    list_filter = ('created_at', 'quantity', 'product__categories')
    search_fields = ('cart__user__email', 'product__name')
    list_per_page = 25
    date_hierarchy = 'created_at'
    raw_id_fields = ('cart', 'product')
    list_display_links = ('get_cart_user', 'get_product_name')
    
    @display(description=_('пользователь'))
    def get_cart_user(self, obj):
        # отображение пользователя корзины
        from django.urls import reverse
        url = reverse('admin:users_user_change', args=[obj.cart.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.cart.user.email)
    
    @display(description=_('товар'))
    def get_product_name(self, obj):
        # отображение названия товара со ссылкой
        from django.urls import reverse
        url = reverse('admin:products_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    
    @display(description=_('цена за шт.'))
    def get_product_price(self, obj):
        # отображение цены за единицу товара
        return f'{obj.product.price} ₽'
    
    @display(description=_('сумма'))
    def get_total_price_display(self, obj):
        # отображение общей стоимости позиции
        return f'{obj.get_total_price()} ₽'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cart', 'cart__user', 'product')
