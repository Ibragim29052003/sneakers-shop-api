"""
Представления для приложения отзывов
"""
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer, ReviewUpdateSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet для модели отзывов."""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        if self.action in ['update', 'partial_update']:
            return ReviewUpdateSerializer
        return ReviewSerializer
    
    def get_queryset(self):
        """Получение отзывов для конкретного товара или пользователя."""
        product_pk = self.kwargs.get('product_pk')
        if product_pk:
            return Review.objects.filter(product_id=product_pk).select_related('user', 'product')
        return Review.objects.filter(user=self.request.user).select_related('user', 'product')
    
    def perform_create(self, serializer):
        """Создание отзыва для товара."""
        product_pk = self.kwargs.get('product_pk') or self.request.data.get('product')
        if not product_pk:
            raise ValidationError({'detail': 'Для создания отзыва нужно передать product.'})

        from products.models import Product

        try:
            serializer.context['product'] = Product.objects.get(pk=product_pk)
        except Product.DoesNotExist as exc:
            raise ValidationError({'detail': 'Товар не найден.'}) from exc

        serializer.save()
    
    def update(self, request, *args, **kwargs):
        """Обновление отзыва - только собственные отзывы."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Проверка, является ли пользователь владельцем отзыва
        if instance.user != request.user:
            return Response(
                {'detail': 'Вы можете редактировать только свои отзывы.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Удаление отзыва - только собственные отзывы."""
        instance = self.get_object()
        
        if instance.user != request.user:
            return Response(
                {'detail': 'Вы можете удалять только свои отзывы.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
