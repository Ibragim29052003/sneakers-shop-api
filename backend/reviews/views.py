"""
Представления для приложения отзывов
"""
from typing import Any

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from core.permissions import IsAdminRole, IsOwnerOrAdmin
from .models import Review
from .serializers import ReviewCreateSerializer, ReviewSerializer, ReviewUpdateSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet для отзывов."""

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self) -> Any:
        """Возвращает данные через `get_serializer_class`."""
        if self.action == 'create':
            return ReviewCreateSerializer
        if self.action in ['update', 'partial_update']:
            return ReviewUpdateSerializer
        return ReviewSerializer
    
    def get_permissions(self) -> Any:
        """Возвращает данные через `get_permissions`."""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        if self.action == 'moderate':
            return [IsAdminRole()]
        return super().get_permissions()

    def get_queryset(self) -> Any:
        """Возвращает данные через `get_queryset`."""
        product_pk = self.kwargs.get('product_pk')
        if product_pk:
            return Review.objects.filter(product_id=product_pk).select_related('user', 'product')
        return Review.objects.select_related('user', 'product')

    def perform_create(self, serializer: Any) -> Any:
        """Выполняет действие `perform_create`."""
        product_pk = self.kwargs.get('product_pk') or self.request.data.get('product')
        if not product_pk:
            raise ValidationError({'detail': 'Для создания отзыва нужно передать product.'})

        from products.models import Product

        try:
            serializer.context['product'] = Product.objects.get(pk=product_pk)
        except Product.DoesNotExist as exc:
            raise ValidationError({'detail': 'Товар не найден.'}) from exc

        serializer.save()
    
    @action(detail=True, methods=['patch'])
    def moderate(self, request: Any, pk: Any=None) -> Any:
        """Выполняет действие `moderate`."""
        review = self.get_object()
        review.is_moderated = request.data.get('is_moderated', True)
        review.save(update_fields=['is_moderated'])
        return Response(ReviewSerializer(review).data)
