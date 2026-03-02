"""
Представления для приложения заказов
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
    """ViewSet для модели статусов заказов."""
    queryset = OrderStatus.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet для модели заказов."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Создание заказа из корзины."""
        with transaction.atomic():
            user = self.request.user
            cart = get_object_or_404(Cart, user=user)
            
            # Создание заказа
            order = serializer.save(user=user)
            
            # Создание товаров в заказе из товаров корзины
            for cart_item in cart.items.all():
                order_item = OrderItem.objects.create(
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
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Обновление статуса заказа."""
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
    """ViewSet для модели товаров в заказе."""
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return OrderItem.objects.filter(order__user=self.request.user)


class ManagerOrdersView(APIView):
    """API view для получения всех заказов менеджерами."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Проверяем, что пользователь - менеджер или админ
        from users.models import UserRole
        is_manager = request.user.user_roles.filter(role__name='manager').exists()
        is_admin = request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists()
        
        if not (is_manager or is_admin):
            return Response(
                {'detail': 'У вас нет доступа к этой информации.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Получаем все заказы
        orders = Order.objects.all().select_related('user', 'status').prefetch_related('items')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
