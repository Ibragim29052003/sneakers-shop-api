"""
Сериализаторы для приложения корзины
"""
from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer
from products.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор для модели товаров в корзине."""
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_id', 'quantity',
            'total_price', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_price(self, obj):
        """Расчет общей стоимости товара."""
        return str(obj.get_total_price())


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели корзины."""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'items', 'total_items',
            'total_price', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'user']
    
    def get_total_items(self, obj):
        """Получение общего количества товаров."""
        return obj.items.count()
    
    def get_total_price(self, obj):
        """Расчет общей стоимости корзины."""
        return str(obj.get_total_price())
