"""
Сериализаторы для приложения отзывов
"""
from rest_framework import serializers
from .models import Review
from users.serializers import UserSerializer
from products.serializers import ProductSerializer


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для модели отзывов."""
    user = UserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    rating_stars = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'product', 'rating', 'rating_stars',
            'comment', 'is_moderated', 'is_verified_purchase',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'product', 'is_moderated', 
            'is_verified_purchase', 'created_at', 'updated_at'
        ]
    
    def get_rating_stars(self, obj):
        """Получение оценки в виде строки со звездами."""
        return '★' * obj.rating + '☆' * (5 - obj.rating)


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания отзывов."""
    
    class Meta:
        model = Review
        fields = ['rating', 'comment']
    
    def validate_rating(self, value):
        """Валидация значения оценки."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Рейтинг должен быть от 1 до 5.')
        return value
    
    def create(self, validated_data):
        """Создание отзыва для товара."""
        user = self.context['request'].user
        product = self.context['product']
        
        # Проверка, оставлял ли пользователь отзыв на этот товар
        if Review.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError(
                {'detail': 'Вы уже оставили отзыв на этот товар.'}
            )
        
        # Проверка, что пользователь действительно покупал товар
        allowed_statuses = ['paid', 'delivered', 'completed']
        has_purchased = product.order_items.filter(
            order__user=user,
            order__status__name__in=allowed_statuses,
        ).exists()
        if not has_purchased:
            raise serializers.ValidationError(
                {'detail': 'Оставлять отзыв могут только покупатели этого товара.'}
            )

        return Review.objects.create(
            user=user,
            product=product,
            is_verified_purchase=True,
            **validated_data,
        )


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления отзывов."""
    
    class Meta:
        model = Review
        fields = ['rating', 'comment']
    
    def validate_rating(self, value):
        """Валидация значения оценки."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Рейтинг должен быть от 1 до 5.')
        return value
