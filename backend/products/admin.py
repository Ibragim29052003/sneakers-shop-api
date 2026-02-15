"""
настройка админки для приложения товаров
"""
from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Category, Product, ProductCategory, ProductImage
from simple_history.admin import SimpleHistoryAdmin


class ProductCategoryInline(admin.TabularInline):
    # inline для отображения связей товар-категория
    model = ProductCategory
    extra = 1
    raw_id_fields = ('product', 'category')


class ProductImageInline(admin.TabularInline):
    # inline для отображения изображений товара
    model = ProductImage
    extra = 0
    readonly_fields = ('created_at', 'image_preview')
    
    @display(description='превью')
    def image_preview(self, obj):
        # отображение превью изображения
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 80px; height: auto;" />',
                obj.image.url
            )
        return ''


class SubcategoryInline(admin.TabularInline):
    # inline для отображения подкатегорий
    model = Category
    extra = 0
    fields = ('name', 'is_active')
    verbose_name = 'подкатегория'
    verbose_name_plural = 'подкатегории'
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(Category)
class CategoryAdmin(SimpleHistoryAdmin):
    # настройка админки для модели категории
    list_display = ('name', 'parent', 'get_is_active_status', 'created_at', 'get_subcategory_count')
    list_filter = ('parent', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    list_per_page = 25
    date_hierarchy = 'created_at'
    raw_id_fields = ('parent',)
    list_display_links = ('name',)
    
    inlines = (SubcategoryInline,)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'parent', 'is_active')
        }),
        (_('даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    @display(description=_('активен'))
    def get_is_active_status(self, obj):
        # отображение статуса активности с цветовой индикацией
        if obj.is_active:
            return format_html('<span style="color: green;">✓ да</span>')
        return format_html('<span style="color: red;">✗ нет</span>')
    
    @display(description=_('подкатегории'))
    def get_subcategory_count(self, obj):
        # отображение количества подкатегорий
        return obj.subcategories.count()
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('subcategories')


@admin.register(Product)
class ProductAdmin(SimpleHistoryAdmin):
    # настройка админки для модели товара
    list_display = ('name', 'sku', 'get_price_display', 'get_is_active_status', 'created_at', 'get_category_list')
    list_filter = ('is_active', 'product_categories__category', 'created_at', 'price')
    search_fields = ('name', 'description', 'sku')
    list_per_page = 25
    date_hierarchy = 'created_at'
    raw_id_fields = ()  # убрали categories из-за связи через ProductCategory
    list_display_links = ('name', 'sku')
    
    inlines = (ProductImageInline, ProductCategoryInline)  # добавили inline для связей
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'sku', 'price', 'is_active')
        }),
        (_('даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    @display(description=_('цена'))
    def get_price_display(self, obj):
        # отображение цены с валютой
        return f'{obj.price} ₽'
    
    @display(description=_('активен'))
    def get_is_active_status(self, obj):
        # отображение статуса активности
        if obj.is_active:
            return format_html('<span style="color: green;">✓ да</span>')
        return format_html('<span style="color: red;">✗ нет</span>')
    
    @display(description=_('категории'))
    def get_category_list(self, obj):
        # отображение списка категорий
        categories = [pc.category.name for pc in obj.product_categories.select_related('category').all()]
        return ', '.join(categories) if categories else '-'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('categories', 'images')


@admin.register(ProductImage)
class ProductImageAdmin(SimpleHistoryAdmin):
    # настройка админки для модели изображений товара
    list_display = ('get_product_name', 'image_preview', 'get_is_main_status', 'created_at')
    list_filter = ('is_main', 'created_at')
    search_fields = ('product__name', 'alt_text')
    list_per_page = 25
    date_hierarchy = 'created_at'
    raw_id_fields = ('product',)
    list_display_links = ('get_product_name',)
    
    @display(description=_('товар'))
    def get_product_name(self, obj):
        # отображение названия товара со ссылкой
        from django.urls import reverse
        url = reverse('admin:products_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    
    @display(description=_('основное'))
    def get_is_main_status(self, obj):
        # отображение статуса основного изображения
        if obj.is_main:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: gray;">-</span>')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


@admin.register(ProductCategory)
class ProductCategoryAdmin(SimpleHistoryAdmin):
    # настройка админки для модели связей товар-категория
    list_display = ('get_product_name', 'get_category_name', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('product__name', 'category__name')
    list_per_page = 25
    date_hierarchy = 'created_at'
    raw_id_fields = ('product', 'category')
    list_display_links = ('get_product_name', 'get_category_name')
    
    @display(description=_('товар'))
    def get_product_name(self, obj):
        # отображение товара со ссылкой
        from django.urls import reverse
        url = reverse('admin:products_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    
    @display(description=_('категория'))
    def get_category_name(self, obj):
        # отображение категории со ссылкой
        from django.urls import reverse
        url = reverse('admin:products_category_change', args=[obj.category.id])
        return format_html('<a href="{}">{}</a>', url, obj.category.name)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'category')
