"""
Сериализаторы для приложения товаров
"""
from rest_framework import serializers
from django.conf import settings
from .models import Category, Product, ProductCategory, ProductImage, SliderImage, FilterGroup, FilterOption, ProductFilter


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для модели категории."""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    subcategories_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'parent', 'parent_name',
            'is_active', 'created_at', 'updated_at', 'subcategories_count'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_subcategories_count(self, obj):
        """Получение количества подкатегорий."""
        return obj.subcategories.count()


class ProductImageSerializer(serializers.ModelSerializer):
    """Сериализатор для модели изображений товара."""
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_main', 'alt_text', 'created_at']
        read_only_fields = ['created_at']
    
    def get_image(self, obj):
        """Получение полного URL изображения."""
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        base_url = getattr(settings, 'BASE_URL', '')
        if not base_url and hasattr(settings, 'DEBUG') and settings.DEBUG:
            base_url = 'http://localhost:8000'
        return f"{base_url}{obj.image.url}"


class SliderImageSerializer(serializers.ModelSerializer):
    """Сериализатор для модели слайдов."""
    image_url = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = SliderImage
        fields = [
            'id', 'title', 'description', 'image', 'image_url',
            'product', 'product_name', 'product_price', 'price', 'old_price',
            'link', 'is_active', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_image_url(self, obj):
        """Получение полного URL изображения."""
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        base_url = getattr(settings, 'BASE_URL', '')
        if not base_url and hasattr(settings, 'DEBUG') and settings.DEBUG:
            base_url = 'http://localhost:8000'
        return f"{base_url}{obj.image.url}"


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для модели товара."""
    images = ProductImageSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    main_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'old_price', 'sku',
            'is_active', 'created_at', 'updated_at', 'categories',
            'images', 'main_image_url', 'external_url'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_media_url(self, relative_url):
        """Построение полного URL для медиафайла."""
        if not relative_url:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(relative_url)
        # Fallback: использовать BASE_URL из настроек или localhost
        base_url = getattr(settings, 'BASE_URL', '')
        if not base_url and hasattr(settings, 'DEBUG') and settings.DEBUG:
            base_url = 'http://localhost:8000'
        return f"{base_url}{relative_url}"
    
    def get_main_image_url(self, obj):
        """Получение URL главного изображения."""
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            return self.get_media_url(main_image.image.url)
        first_image = obj.images.first()
        if first_image:
            return self.get_media_url(first_image.image.url)
        return None


class ProductCategorySerializer(serializers.ModelSerializer):
    """Сериализатор для модели связи товаров и категорий."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ProductCategory
        fields = ['id', 'product', 'product_name', 'category', 'category_name', 'created_at']
        read_only_fields = ['created_at']


class FilterOptionSerializer(serializers.ModelSerializer):
    """Сериализатор для значений фильтров."""
    
    class Meta:
        model = FilterOption
        fields = ['id', 'name', 'is_active', 'order']
        read_only_fields = ['created_at']


class FilterGroupSerializer(serializers.ModelSerializer):
    """Сериализатор для групп фильтров."""
    options = FilterOptionSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = FilterGroup
        fields = ['id', 'name', 'category', 'category_name', 'options', 'is_active', 'order', 'created_at']
        read_only_fields = ['created_at']


class ProductFilterSerializer(serializers.ModelSerializer):
    """Сериализатор для связи товаров и фильтров."""
    option_name = serializers.CharField(source='filter_option.name', read_only=True)
    option_value = serializers.CharField(source='filter_option.value', read_only=True)
    group_name = serializers.CharField(source='filter_option.group.name', read_only=True)
    
    class Meta:
        model = ProductFilter
        fields = ['id', 'product', 'filter_option', 'option_name', 'option_value', 'group_name', 'created_at']
        read_only_fields = ['created_at']


class FilterGroupByCategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения групп фильтров по категории.
    Возвращает структуру, удобную для фронтенда.
    """
    options = FilterOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = FilterGroup
        fields = ['id', 'name', 'options', 'order']
