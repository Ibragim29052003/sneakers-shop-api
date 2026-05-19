"""
Представления для приложения заказов
"""
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db import transaction
from .models import OrderStatus, Order, OrderItem
from .serializers import OrderStatusSerializer, OrderSerializer, OrderItemSerializer, OrderCreateSerializer


class OrderStatusViewSet(viewsets.ModelViewSet):
    """ViewSet для модели статусов заказов."""
    queryset = OrderStatus.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet для модели заказов."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        is_admin = self.request.user.is_staff or self.request.user.user_roles.filter(role__name='admin').exists()
        queryset = Order.objects.select_related('user', 'status').prefetch_related('items__product')
        if is_admin:
            return queryset
        return queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Создание заказа из корзины."""
        serializer.save()
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Обновление заказа. Смена статуса доступна только администратору/менеджеру."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        is_admin = request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists()
        is_manager = request.user.user_roles.filter(role__name='manager').exists()

        if not (is_admin or is_manager):
            raise PermissionDenied('Только администратор или менеджер может изменять заказ.')

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class OrderItemViewSet(viewsets.ModelViewSet):
    """ViewSet для модели товаров в заказе."""
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return OrderItem.objects.filter(order__user=self.request.user).select_related('order', 'product')


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
