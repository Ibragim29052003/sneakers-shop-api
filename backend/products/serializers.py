"""
Сериализаторы для приложения товаров
"""
from rest_framework import serializers
from .models import Category, Product, ProductCategory, ProductImage


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
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_main', 'alt_text', 'created_at']
        read_only_fields = ['created_at']


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для модели товара."""
    images = ProductImageSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    main_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'sku',
            'is_active', 'created_at', 'updated_at', 'categories',
            'images', 'main_image_url', 'external_url'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_main_image_url(self, obj):
        """Получение URL главного изображения."""
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            return main_image.image.url
        first_image = obj.images.first()
        if first_image:
            return first_image.image.url
        return None


class ProductCategorySerializer(serializers.ModelSerializer):
    """Сериализатор для модели связи товаров и категорий."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ProductCategory
        fields = ['id', 'product', 'product_name', 'category', 'category_name', 'created_at']
        read_only_fields = ['created_at']
