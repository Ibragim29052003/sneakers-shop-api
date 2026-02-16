"""
Представления для приложения корзины
"""
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


class CartViewSet(viewsets.ModelViewSet):
    """ViewSet для модели корзины."""
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Получение или создание корзины для пользователя."""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart
    
    def list(self, request, *args, **kwargs):
        """Получение корзины текущего пользователя."""
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)


class CartItemViewSet(viewsets.ModelViewSet):
    """ViewSet для модели товаров в корзине."""
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)
    
    def perform_create(self, serializer):
        """Добавление товара в корзину."""
        cart = get_object_or_404(Cart, user=self.request.user)
        product = serializer.validated_data.get('product')
        quantity = serializer.validated_data.get('quantity', 1)
        
        # Проверка, есть ли товар уже в корзине
        existing_item = CartItem.objects.filter(cart=cart, product=product).first()
        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
            return existing_item
        
        serializer.save(cart=cart)
    
    def update(self, request, *args, **kwargs):
        """Обновление количества товара в корзине."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        quantity = request.data.get('quantity')
        
        if quantity is not None:
            instance.quantity = int(quantity)
            instance.save()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
