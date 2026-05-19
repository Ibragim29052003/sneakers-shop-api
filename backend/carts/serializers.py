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

    def validate(self, attrs):
        """Проверка наличия товара на складе."""
        product = attrs.get('product')
        quantity = attrs.get('quantity', 1)

        if not product:
            return attrs

        if quantity <= 0:
            raise serializers.ValidationError({'detail': 'Количество товара должно быть больше 0.'})

        if product.stock_quantity <= 0 or product.status in ['draft', 'out_of_stock', 'archived']:
            raise serializers.ValidationError({'detail': 'Товар недоступен для добавления в корзину.'})

        request = self.context.get('request')
        current_quantity = 0
        if request and request.user.is_authenticated:
            from carts.models import CartItem

            qs = CartItem.objects.filter(cart__user=request.user, product=product)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            current_quantity = sum(item.quantity for item in qs)

        if quantity + current_quantity > product.stock_quantity:
            raise serializers.ValidationError(
                {'detail': f'Недостаточно товара на складе. Доступно: {product.stock_quantity}.'}
            )

        return attrs
    
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
