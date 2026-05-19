"""
Сериализаторы для приложения заказов
"""
import re
from decimal import Decimal

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
    
    MIN_ORDER_TOTAL = Decimal('500.00')
    MAX_ORDER_TOTAL = Decimal('100000.00')
    SHIPPING_ADDRESS_PATTERN = r'^.+,\s*д\.?\s*\d+[\w\-/]*,\s*.+,\s*\d{6}$'

    class Meta:
        model = Order
        fields = ['shipping_address', 'notes']

    def validate_shipping_address(self, value):
        """Валидация адреса доставки: улица, дом, город, индекс."""
        if not re.match(self.SHIPPING_ADDRESS_PATTERN, value.strip(), flags=re.IGNORECASE):
            raise serializers.ValidationError(
                'Адрес должен быть в формате: "Улица Пушкина, д 10, Москва, 123456".'
            )
        return value
    
    def create(self, validated_data):
        """Создание заказа из корзины."""
        user = self.context['request'].user
        from carts.models import Cart
        from django.db import transaction
        from products.models import Product

        with transaction.atomic():
            cart, _ = Cart.objects.get_or_create(user=user)
            if not cart.items.exists():
                raise serializers.ValidationError({'detail': 'Нельзя оформить пустой заказ.'})

            cart_items = list(cart.items.select_related('product'))
            product_ids = [item.product_id for item in cart_items]
            products_by_id = {
                product.id: product
                for product in Product.objects.select_for_update().filter(id__in=product_ids)
            }

            for cart_item in cart_items:
                product = products_by_id.get(cart_item.product_id)
                if not product or product.stock_quantity <= 0 or product.status == 'out_of_stock':
                    raise serializers.ValidationError(
                        {'detail': f'Товар "{cart_item.product.name}" недоступен для заказа.'}
                    )
                if cart_item.quantity > product.stock_quantity:
                    raise serializers.ValidationError(
                        {'detail': f'Недостаточно товара "{product.name}" на складе.'}
                    )

            expected_total = sum(
                (products_by_id[cart_item.product_id].price * cart_item.quantity) for cart_item in cart_items
            )
            if expected_total <= 0:
                raise serializers.ValidationError({'detail': 'Сумма заказа должна быть больше 0 рублей.'})
            if expected_total < self.MIN_ORDER_TOTAL or expected_total > self.MAX_ORDER_TOTAL:
                raise serializers.ValidationError(
                    {'detail': 'Сумма заказа должна быть от 500 до 100000 рублей.'}
                )

            order = Order.objects.create(user=user, total=expected_total, **validated_data)

            for cart_item in cart_items:
                product = products_by_id[cart_item.product_id]
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_sku=product.sku,
                    price=product.price,
                    quantity=cart_item.quantity
                )
                product.stock_quantity -= cart_item.quantity
                product.save(update_fields=['stock_quantity'])

            cart.items.all().delete()
            return order
