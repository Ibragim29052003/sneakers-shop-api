"""
Представления для приложения поставщиков
"""
from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import (
    Supplier,
    SupplierContract,
    ContractDocument,
    SupplierProductRequest,
    RequestDocument,
    SupplierProduct,
    SystemAlert,
    ContractStatus,
    RequestStatus,
    DocumentType,
    AlertType,
    ProductSupplierSource,
)
from .serializers import (
    SupplierSerializer,
    SupplierRegisterSerializer,
    SupplierApplySerializer,
    SupplierWithRequestSerializer,
    SupplierContractSerializer,
    ContractDocumentSerializer,
    SupplierProductRequestSerializer,
    SupplierProductRequestCreateSerializer,
    SupplierProductRequestManageSerializer,
    RequestDocumentSerializer,
    SupplierProductSerializer,
    SystemAlertSerializer,
    SystemAlertCreateSerializer,
    ContractStatusSerializer,
    RequestStatusSerializer,
    DocumentTypeSerializer,
    AlertTypeSerializer,
    ProductSupplierSourceSerializer,
)
from .permissions import (
    IsAdminUser,
    IsUser,
    IsManagerOrAdmin,
    IsOwnerOrReadOnly,
    IsAdminOrReadOnly,
    IsManagerForRequest,
    CanManageSupplierRequests,
    CanAssignManager,
    IsAuthenticatedOrReadOnlyForPublic,
    IsSupplierOrReadOnly,
)


# ==================== Справочники ====================

class ContractStatusViewSet(viewsets.ModelViewSet):
    """ViewSet для модели статусов договоров."""
    queryset = ContractStatus.objects.all()
    serializer_class = ContractStatusSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class RequestStatusViewSet(viewsets.ModelViewSet):
    """ViewSet для модели статусов заявок."""
    queryset = RequestStatus.objects.all()
    serializer_class = RequestStatusSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class DocumentTypeViewSet(viewsets.ModelViewSet):
    """ViewSet для модели типов документов."""
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class AlertTypeViewSet(viewsets.ModelViewSet):
    """ViewSet для модели типов уведомлений."""
    queryset = AlertType.objects.all()
    serializer_class = AlertTypeSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class ProductSupplierSourceViewSet(viewsets.ModelViewSet):
    """ViewSet для модели источников товара."""
    queryset = ProductSupplierSource.objects.all()
    serializer_class = ProductSupplierSourceSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


# ==================== Поставщики ====================

class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet для модели поставщиков."""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'inn', 'contact_person', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


# ==================== Договоры ====================

class SupplierContractViewSet(viewsets.ModelViewSet):
    """ViewSet для модели договоров поставщиков."""
    queryset = SupplierContract.objects.all()
    serializer_class = SupplierContractSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'status']
    search_fields = ['contract_number', 'title', 'description']
    ordering_fields = ['created_at', 'end_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Фильтрация по истекающим договорам
        expiring_soon = self.request.query_params.get('expiring_soon')
        if expiring_soon == 'true':
            from datetime import timedelta
            queryset = queryset.filter(
                end_date__gte=timezone.now().date(),
                end_date__lte=timezone.now().date() + timedelta(days=30)
            )
        return queryset


class ContractDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet для модели документов договоров."""
    queryset = ContractDocument.objects.all()
    serializer_class = ContractDocumentSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['contract', 'document_type']
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


# ==================== Заявки на поставку ====================

class SupplierProductRequestViewSet(viewsets.ModelViewSet):
    """ViewSet для модели заявок на поставку товара."""
    queryset = SupplierProductRequest.objects.all()
    serializer_class = SupplierProductRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'status']
    search_fields = ['product_name', 'product_sku', 'product_description']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SupplierProductRequestCreateSerializer
        if self.action in ['update', 'partial_update']:
            # Проверка прав администратора или менеджера заявки
            return SupplierProductRequestManageSerializer
        return SupplierProductRequestSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [IsAuthenticated()]
        return [CanManageSupplierRequests()]
    
    def get_queryset(self):
        user = self.request.user
        # Админ видит все заявки
        if user.is_staff or user.user_roles.filter(role__name='admin').exists():
            return SupplierProductRequest.objects.all()
        # Менеджер видит свои назначенные заявки
        if hasattr(self, 'action') and self.action in ['list', 'retrieve']:
            return SupplierProductRequest.objects.filter(
                manager_id=user.id
            ) | SupplierProductRequest.objects.filter(supplier__contact_person=user.email)
        return SupplierProductRequest.objects.filter(manager_id=user.id)
    
    def perform_create(self, serializer):
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        """Обновление заявки - для управления (одобрения/отклонения) заявок."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Проверка прав
        if not request.user.is_staff and not request.user.user_roles.filter(role__name='admin').exists():
            if instance.manager_id != request.user.id:
                return Response(
                    {'detail': 'Вы не являетесь менеджером этой заявки.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Если статус изменяется на одобрено/отклонено, установить reviewed_by и reviewed_at
        if 'status' in request.data and instance.status.name not in ['approved', 'rejected']:
            instance.reviewed_by = request.user
            instance.reviewed_at = timezone.now()
            instance.save()
        
        self.perform_update(serializer)
        return Response(serializer.data)


class AssignManagerView(APIView):
    """API view для назначения менеджера заявки поставщика."""
    permission_classes = [CanAssignManager]
    
    def post(self, request, request_id):
        """Назначение менеджера заявке поставщика."""
        supplier_request = get_object_or_404(SupplierProductRequest, id=request_id)
        manager_id = request.data.get('manager_id')
        
        if not manager_id:
            return Response(
                {'detail': 'manager_id обязателен.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from users.models import User
        manager = get_object_or_404(User, id=manager_id)
        
        supplier_request.manager = manager
        supplier_request.save()
        
        # Создание уведомления для менеджера
        try:
            alert_type = AlertType.objects.get(name='request_waiting_review')
            SystemAlert.objects.create(
                alert_type=alert_type,
                user=manager,
                title='Назначен менеджером заявки',
                message=f'Вы назначены менеджером заявки #{supplier_request.id} на товар "{supplier_request.product_name}"',
                request=supplier_request
            )
        except AlertType.DoesNotExist:
            pass  # Игнорируем если тип уведомления не существует
        
        return Response(
            {'detail': f'Менеджер {manager.email} назначен для заявки #{supplier_request.id}'},
            status=status.HTTP_200_OK
        )


class CreateProductFromRequestView(APIView):
    """API view для создания товара поставщика из одобренной заявки."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, request_id):
        """Создание товара поставщика из заявки."""
        supplier_request = get_object_or_404(SupplierProductRequest, id=request_id)
        
        # Проверяем, что заявка одобрена
        if supplier_request.status.name != 'approved':
            return Response(
                {'detail': 'Можно создавать товар только из одобренной заявки.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, что товар ещё не создан
        if hasattr(supplier_request, '_product_created') and supplier_request._product_created:
            return Response(
                {'detail': 'Товар уже был создан из этой заявки.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Получаем данные из запроса
        product_id = request.data.get('product')
        
        if not product_id:
            return Response(
                {'detail': 'product обязателен.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from products.models import Product
        product = get_object_or_404(Product, id=product_id)
        
        # Проверяем, не существует ли уже такая связь
        existing = SupplierProduct.objects.filter(supplier=supplier_request.supplier, product=product).first()
        if existing:
            return Response(
                {'detail': 'Связь между этим поставщиком и товаром уже существует.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаём товар поставщика
        supplier_product = SupplierProduct.objects.create(
            supplier=supplier_request.supplier,
            product=product,
            supplier_sku=supplier_request.product_sku or '',
            supplier_price=supplier_request.suggested_price,
            notes=supplier_request.notes or ''
        )
        
        # Помечаем заявку как обработанную
        supplier_request._product_created = True
        supplier_request.save(update_fields=['updated_at'])
        
        serializer = SupplierProductSerializer(supplier_product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RequestDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet для модели документов заявок."""
    queryset = RequestDocument.objects.all()
    serializer_class = RequestDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['request', 'document_type']
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.user_roles.filter(role__name='admin').exists():
            return RequestDocument.objects.all()
        return RequestDocument.objects.filter(
            request__manager_id=user.id
        ) | RequestDocument.objects.filter(uploaded_by=user)
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


# ==================== Поставки товаров ====================

class SupplierProductViewSet(viewsets.ModelViewSet):
    """ViewSet для модели поставок товаров."""
    queryset = SupplierProduct.objects.all()
    serializer_class = SupplierProductSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'product', 'is_preferred']
    search_fields = ['supplier__name', 'product__name', 'supplier_sku']
    ordering_fields = ['created_at', 'supplier__name']
    ordering = ['-is_preferred', 'supplier__name']


# ==================== Системные уведомления ====================

class SystemAlertViewSet(viewsets.ModelViewSet):
    """ViewSet для модели системных уведомлений."""
    queryset = SystemAlert.objects.all()
    serializer_class = SystemAlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['alert_type', 'is_read']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        # Админ видит все уведомления
        if user.is_staff or user.user_roles.filter(role__name='admin').exists():
            return SystemAlert.objects.all()
        # Обычные пользователи видят только свои уведомления
        return SystemAlert.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SystemAlertCreateSerializer
        return SystemAlertSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        """Отметка уведомления как прочитанного."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Проверка, является ли пользователь владельцем уведомления или админом
        if instance.user != request.user:
            if not (request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists()):
                return Response(
                    {'detail': 'Вы не можете изменять чужие уведомления.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Если отмечается как прочитанное, установить read_by и read_at
        if 'is_read' in request.data and request.data['is_read'] and not instance.is_read:
            instance.read_by = request.user
            instance.read_at = timezone.now()
            instance.save()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def mark_as_read(self, request, pk=None):
        """Отметка конкретного уведомления как прочитанного."""
        alert = get_object_or_404(SystemAlert, id=pk, user=request.user)
        alert.is_read = True
        alert.read_by = request.user
        alert.read_at = timezone.now()
        alert.save()
        return Response({'detail': 'Уведомление помечено как прочитанное.'})


class UserAlertsView(APIView):
    """API view для получения уведомлений текущего пользователя."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Получение уведомлений текущего пользователя."""
        alerts = SystemAlert.objects.filter(user=request.user)
        unread_count = alerts.filter(is_read=False).count()
        serializer = SystemAlertSerializer(alerts, many=True)
        return Response({
            'count': alerts.count(),
            'unread_count': unread_count,
            'alerts': serializer.data
        })
    
    def post(self, request):
        """Отметка всех уведомлений как прочитанных."""
        SystemAlert.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_by=request.user,
            read_at=timezone.now()
        )
        return Response({'detail': 'Все уведомления помечены как прочитанные.'})


# ==================== Регистрация поставщиков ====================

class SupplierRegisterView(APIView):
    """
    API view для регистрации нового поставщика.
    Публичный эндпоинт - регистрация нового пользователя и поставщика.
    """
    permission_classes = []  # Публичный доступ
    
    def post(self, request):
        """Регистрация нового поставщика с созданием пользователя."""
        serializer = SupplierRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = serializer.save()
        
        return Response(
            SupplierSerializer(supplier).data,
            status=status.HTTP_201_CREATED
        )


class SupplierApplyView(APIView):
    """
    API view для подачи заявки на регистрацию поставщика от существующего пользователя.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Подача заявки на регистрацию поставщика."""
        # Проверяем, не является ли пользователь уже поставщиком
        if hasattr(request.user, 'supplier_profile') and request.user.supplier_profile:
            return Response(
                {'detail': 'Вы уже являетесь поставщиком.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SupplierApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Создаём поставщика с привязкой к текущему пользователю
        supplier = Supplier.objects.create(
            user=request.user,
            **serializer.validated_data
        )
        
        # Назначаем роль поставщика
        from users.models import Role, UserRole
        supplier_role, _ = Role.objects.get_or_create(
            name='supplier',
            defaults={'description': 'Поставщик товаров'}
        )
        UserRole.objects.get_or_create(user=request.user, role=supplier_role)
        
        return Response(
            SupplierSerializer(supplier).data,
            status=status.HTTP_201_CREATED
        )


class MySupplierProfileView(APIView):
    """
    API view для получения профиля поставщика текущего пользователя.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Получение профиля поставщика текущего пользователя."""
        try:
            supplier = Supplier.objects.get(user=request.user)
            serializer = SupplierSerializer(supplier)
            return Response(serializer.data)
        except Supplier.DoesNotExist:
            return Response(
                {'detail': 'Вы не являетесь поставщиком.'},
                status=status.HTTP_404_NOT_FOUND
            )


class RegisterSupplierWithRequestView(APIView):
    """
    Упрощённая регистрация поставщика с заявкой на товар.
    
    Пользователь заполняет одну форму:
    - Данные компании
    - Предлагаемый товар
    
    Система создаёт:
    1. User с ролью supplier
    2. Supplier
    3. SupplierProductRequest со статусом PENDING
    
    Админ потом рассматривает заявку и одобряет/отклоняет.
    """
    permission_classes = []  # Публичный эндпоинт
    
    def post(self, request):
        """Регистрация поставщика с заявкой на товар."""
        serializer = SupplierWithRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        result = serializer.save()
        
        # Сериализуем результат
        supplier_serializer = SupplierSerializer(result['supplier'])
        request_serializer = SupplierProductRequestSerializer(result['product_request'])
        
        return Response({
            'supplier': supplier_serializer.data,
            'product_request': request_serializer.data,
            'message': 'Заявка отправлена на рассмотрение. Ожидайте одобрения от администратора.'
        }, status=status.HTTP_201_CREATED)
