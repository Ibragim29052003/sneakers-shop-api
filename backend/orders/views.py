"""
Представления для приложения заказов
"""
from typing import Any

from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from core.permissions import IsAdminRole, IsOrderOwnerOrAdmin
from .models import OrderStatus, Order, OrderItem
from .serializers import OrderStatusSerializer, OrderSerializer, OrderItemSerializer, OrderCreateSerializer
from .tasks import send_order_created_email, send_order_status_changed_email


class OrderStatusViewSet(viewsets.ModelViewSet):
    """ViewSet для модели статусов заказов."""
    queryset = OrderStatus.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [IsAdminRole]


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet для модели заказов."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> Any:
        """Возвращает данные через `get_serializer_class`."""
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def get_queryset(self) -> Any:
        """Возвращает данные через `get_queryset`."""
        is_admin = self.request.user.is_staff or self.request.user.user_roles.filter(role__name='admin').exists()
        queryset = Order.objects.select_related('user', 'status').prefetch_related('items__product')
        if is_admin:
            return queryset
        return queryset.filter(user=self.request.user)

    def get_permissions(self) -> Any:
        """Возвращает данные через `get_permissions`."""
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated()]
        if self.action in ['retrieve', 'destroy']:
            return [IsAuthenticated(), IsOrderOwnerOrAdmin()]
        return super().get_permissions()
    
    def perform_create(self, serializer: Any) -> Any:
        """Создание заказа из корзины."""
        order = serializer.save()
        send_order_created_email.delay(order.id)
    
    @transaction.atomic
    def update(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        """Обновление заказа. Смена статуса доступна только администратору/менеджеру."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        is_admin = request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists()
        is_manager = request.user.user_roles.filter(role__name='manager').exists()

        if not (is_admin or is_manager):
            raise PermissionDenied('Только администратор или менеджер может изменять заказ.')

        if 'status' not in request.data:
            raise ValidationError({'status': 'Для обновления заказа нужно передать поле status.'})

        forbidden_fields = [field for field in request.data.keys() if field != 'status']
        if forbidden_fields:
            raise PermissionDenied('Разрешено изменять только статус заказа.')

        previous_status_id = instance.status_id
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if previous_status_id != serializer.instance.status_id:
            send_order_status_changed_email.delay(serializer.instance.id)

        return Response(serializer.data)


class OrderItemViewSet(viewsets.ModelViewSet):
    """ViewSet для модели товаров в заказе."""
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self) -> Any:
        """Возвращает данные через `get_queryset`."""
        return OrderItem.objects.filter(order__user=self.request.user).select_related('order', 'product')


class ManagerOrdersView(APIView):
    """API view для получения всех заказов менеджерами."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Any) -> Any:
        # Проверяем, что пользователь - менеджер или админ
        """Выполняет действие `get`."""
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
