"""
Сериализаторы для приложения заказов
"""
from rest_framework import serializers
from .models import OrderStatus, Order, OrderItem
from users.serializers import UserSerializer


class OrderStatusSerializer(serializers.ModelSerializer):
    """Сериализатор для модели статусов заказов."""
    
    class Meta:
        model = OrderStatus
        fields = ['id', 'name', 'description', 'is_final', 'created_at']
        read_only_fields = ['created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для модели товаров в заказе."""
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'price', 'quantity', 'get_total_price', 'created_at'
        ]
        read_only_fields = ['created_at']


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для модели заказов."""
    items = OrderItemSerializer(many=True, read_only=True)
    status_info = OrderStatusSerializer(source='status', read_only=True)
    user = UserSerializer(read_only=True)
    total_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'status', 'status_info', 'total', 'total_display',
            'shipping_address', 'notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'user', 'total']
    
    def get_total_display(self, obj):
        """Получение общей суммы в виде строки."""
        return str(obj.total)


class OrderCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания заказов."""
    
    class Meta:
        model = Order
        fields = ['status', 'shipping_address', 'notes']
    
    def create(self, validated_data):
        """Создание заказа из корзины."""
        user = self.context['request'].user
        from carts.models import Cart
        from django.db import transaction
        
        with transaction.atomic():
            cart = Cart.objects.get(user=user)
            order = Order.objects.create(user=user, **validated_data)
            
            # Создание товаров в заказе
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    product_sku=cart_item.product.sku,
                    price=cart_item.product.price,
                    quantity=cart_item.quantity
                )
            
            # Расчет общей суммы
            order.calculate_total()
            
            # Очистка корзины
            cart.items.all().delete()
            
            return order
