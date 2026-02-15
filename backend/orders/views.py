"""
Views for orders app.
"""
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import OrderStatus, Order, OrderItem
from .serializers import OrderStatusSerializer, OrderSerializer, OrderItemSerializer
from carts.models import Cart
from products.models import Product


class OrderStatusViewSet(viewsets.ModelViewSet):
    """ViewSet for OrderStatus model."""
    queryset = OrderStatus.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Order model."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create order from cart."""
        with transaction.atomic():
            user = self.request.user
            cart = get_object_or_404(Cart, user=user)
            
            # Create order
            order = serializer.save(user=user)
            
            # Create order items from cart items
            for cart_item in cart.items.all():
                order_item = OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    product_sku=cart_item.product.sku,
                    price=cart_item.product.price,
                    quantity=cart_item.quantity
                )
            
            # Calculate total
            order.calculate_total()
            
            # Clear cart
            cart.items.all().delete()
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Update order status."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        status_id = request.data.get('status')
        
        if status_id:
            instance.status_id = status_id
            instance.save()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class OrderItemViewSet(viewsets.ModelViewSet):
    """ViewSet for OrderItem model."""
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return OrderItem.objects.filter(order__user=self.request.user)
