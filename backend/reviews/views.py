"""
Представления для приложения отзывов
"""
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet для модели отзывов."""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Получение отзывов для конкретного товара или пользователя."""
        product_pk = self.kwargs.get('product_pk')
        if product_pk:
            return Review.objects.filter(product_id=product_pk)
        return Review.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Создание отзыва для товара."""
        product_pk = self.kwargs.get('product_pk')
        if product_pk:
            serializer.save(
                user=self.request.user,
                product_id=product_pk
            )
        else:
            serializer.save(user=self.request.user)
    
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
