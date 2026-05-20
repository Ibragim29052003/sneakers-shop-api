"""
Представления для приложения поставщиков
"""
from typing import Any

from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

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
    RequestCommunication,
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
    RequestCommunicationSerializer,
    RequestCommunicationCreateSerializer,
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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'inn', 'contact_person', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_permissions(self) -> Any:
        # Создание, редактирование, удаление - только админ
        # Чтение - все авторизованные
        """Возвращает данные через `get_permissions`."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]


# ==================== Договоры ====================

class SupplierContractViewSet(viewsets.ModelViewSet):
    """ViewSet для модели договоров поставщиков."""
    queryset = SupplierContract.objects.all()
    serializer_class = SupplierContractSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'status']
    search_fields = ['contract_number', 'title', 'description']
    ordering_fields = ['created_at', 'end_date']
    ordering = ['-created_at']
    
    def get_permissions(self) -> Any:
        # Создание, редактирование, удаление - только админ
        # Чтение - все авторизованные
        """Возвращает данные через `get_permissions`."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self) -> Any:
        """Возвращает данные через `get_queryset`."""
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
    
    def perform_create(self, serializer: Any) -> Any:
        """Выполняет действие `perform_create`."""
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
    
    def get_serializer_class(self) -> Any:
        """Возвращает данные через `get_serializer_class`."""
        if self.action == 'create':
            return SupplierProductRequestCreateSerializer
        if self.action in ['update', 'partial_update']:
            # Проверка прав администратора или менеджера заявки
            return SupplierProductRequestManageSerializer
        return SupplierProductRequestSerializer
    
    def get_permissions(self) -> Any:
        """Возвращает данные через `get_permissions`."""
        if self.action in ['create', 'list', 'retrieve']:
            return [IsAuthenticated()]
        return [CanManageSupplierRequests()]
    
    def get_queryset(self) -> Any:
        """Возвращает данные через `get_queryset`."""
        user = self.request.user
        search_query = (self.request.query_params.get('search') or '').strip()
        case_sensitive = self.request.query_params.get('case_sensitive', 'false').lower() == 'true'

        # Админ видит все заявки
        if user.is_staff or user.user_roles.filter(role__name='admin').exists():
            queryset = SupplierProductRequest.objects.all()
        # Менеджер видит свои назначенные заявки
        elif hasattr(self, 'action') and self.action in ['list', 'retrieve']:
            queryset = SupplierProductRequest.objects.filter(
                manager_id=user.id
            ) | SupplierProductRequest.objects.filter(supplier__contact_person=user.email)
        else:
            queryset = SupplierProductRequest.objects.filter(manager_id=user.id)

        if search_query:
            lookup = 'contains' if case_sensitive else 'icontains'
            search_filter = (
                Q(**{f'product_name__{lookup}': search_query}) |
                Q(**{f'product_sku__{lookup}': search_query}) |
                Q(**{f'product_description__{lookup}': search_query}) |
                Q(**{f'notes__{lookup}': search_query}) |
                Q(**{f'supplier__name__{lookup}': search_query})
            )
            queryset = queryset.filter(search_filter)

        return queryset.distinct()
    
    def perform_create(self, serializer: Any) -> Any:
        """Выполняет действие `perform_create`."""
        serializer.save()
    
    def update(self, request: Any, *args: Any, **kwargs: Any) -> Any:
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
    
    def post(self, request: Any, request_id: Any) -> Any:
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


class UploadProductImageView(APIView):
    """API view для загрузки изображений товара поставщика."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request: Any) -> Any:
        """Загрузка изображения товара."""
        image_file = request.FILES.get('image')
        
        if not image_file:
            return Response(
                {'detail': 'Изображение обязательно.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка типа файла
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        if image_file.content_type not in allowed_types:
            return Response(
                {'detail': 'Недопустимый тип файла. Разрешены: JPEG, PNG, WebP, GIF.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка размера файла (максимум 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return Response(
                {'detail': 'Размер файла не должен превышать 10MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Сохраняем файл
        from django.core.files.storage import default_storage
        from django.utils import timezone
        import os
        
        # Создаём директорию с датой
        now = timezone.now()
        upload_dir = f'supplier_products/{now.year}/{now.month:02d}/{now.day:02d}'
        file_path = os.path.join(upload_dir, image_file.name)
        
        # Сохраняем файл
        saved_path = default_storage.save(file_path, image_file)
        
        # Получаем URL файла
        file_url = default_storage.url(saved_path)
        
        return Response(
            {'url': file_url, 'file_name': image_file.name},
            status=status.HTTP_201_CREATED
        )


class CreateProductFromRequestView(APIView):
    """API view для создания товара поставщика из одобренной заявки."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request: Any, request_id: Any) -> Any:
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
    
    def get_queryset(self) -> Any:
        """Возвращает данные через `get_queryset`."""
        user = self.request.user
        if user.is_staff or user.user_roles.filter(role__name='admin').exists():
            return RequestDocument.objects.all()
        return RequestDocument.objects.filter(
            request__manager_id=user.id
        ) | RequestDocument.objects.filter(uploaded_by=user)
    
    def perform_create(self, serializer: Any) -> Any:
        """Выполняет действие `perform_create`."""
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
    
    def get_queryset(self) -> Any:
        """Возвращает данные через `get_queryset`."""
        user = self.request.user
        # Админ видит все уведомления
        if user.is_staff or user.user_roles.filter(role__name='admin').exists():
            return SystemAlert.objects.all()
        # Обычные пользователи видят только свои уведомления
        return SystemAlert.objects.filter(user=user)
    
    def get_serializer_class(self) -> Any:
        """Возвращает данные через `get_serializer_class`."""
        if self.action == 'create':
            return SystemAlertCreateSerializer
        return SystemAlertSerializer
    
    def perform_create(self, serializer: Any) -> Any:
        """Выполняет действие `perform_create`."""
        serializer.save()
    
    def update(self, request: Any, *args: Any, **kwargs: Any) -> Any:
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
    
    def mark_as_read(self, request: Any, pk: Any=None) -> Any:
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
    
    def get(self, request: Any) -> Any:
        """Получение уведомлений текущего пользователя."""
        alerts = SystemAlert.objects.filter(user=request.user)
        unread_count = alerts.filter(is_read=False).count()
        serializer = SystemAlertSerializer(alerts, many=True)
        return Response({
            'count': alerts.count(),
            'unread_count': unread_count,
            'alerts': serializer.data
        })
    
    def post(self, request: Any) -> Any:
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
    permission_classes = [AllowAny]
    throttle_scope = 'supplier_registration'
    
    def post(self, request: Any) -> Any:
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
    
    def post(self, request: Any) -> Any:
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
    
    def get(self, request: Any) -> Any:
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
    permission_classes = [AllowAny]
    throttle_scope = 'supplier_registration'
    
    def post(self, request: Any) -> Any:
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


# ==================== Коммуникации по заявкам ====================

class RequestCommunicationViewSet(viewsets.ModelViewSet):
    """ViewSet для коммуникаций по заявкам поставщиков."""
    queryset = RequestCommunication.objects.all()
    serializer_class = RequestCommunicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['request', 'direction']
    ordering_fields = ['created_at']
    ordering = ['created_at']
    
    def get_queryset(self) -> Any:
        """Возвращает данные через `get_queryset`."""
        user = self.request.user
        # Админ видит все коммуникации
        if user.is_staff or user.user_roles.filter(role__name='admin').exists():
            return RequestCommunication.objects.all()
        # Менеджер видит коммуникации по своим заявкам
        if hasattr(user, 'managed_requests'):
            return RequestCommunication.objects.filter(
                request__manager_id=user.id
            )
        # Поставщик видит коммуникации по своим заявкам
        if hasattr(user, 'supplier_profile') and user.supplier_profile:
            return RequestCommunication.objects.filter(
                request__supplier=user.supplier_profile
            )
        return RequestCommunication.objects.none()
    
    def get_serializer_class(self) -> Any:
        """Возвращает данные через `get_serializer_class`."""
        if self.action == 'create':
            return RequestCommunicationCreateSerializer
        return RequestCommunicationSerializer
    
    def perform_create(self, serializer: Any) -> Any:
        """Выполняет действие `perform_create`."""
        user = self.request.user
        request_obj = serializer.validated_data['request']
        
        # Определяем направление сообщения
        direction = RequestCommunication.FROM_MANAGER
        
        # Если пользователь - поставщик этой заявки
        if hasattr(user, 'supplier_profile') and user.supplier_profile:
            if request_obj.supplier_id == user.supplier_profile.id:
                direction = RequestCommunication.FROM_SUPPLIER
        # Если пользователь - менеджер этой заявки
        elif request_obj.manager_id == user.id:
            direction = RequestCommunication.FROM_MANAGER
        # Если админ - тоже от менеджера
        elif user.is_staff or user.user_roles.filter(role__name='admin').exists():
            direction = RequestCommunication.FROM_MANAGER
        
        serializer.save(sender=user, direction=direction)


class RequestCommunicationByRequestView(APIView):
    """API view для получения коммуникаций по конкретной заявке."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Any, request_id: Any) -> Any:
        """Получение всех сообщений по заявке."""
        supplier_request = get_object_or_404(SupplierProductRequest, id=request_id)
        user = request.user
        
        # Проверка доступа
        is_admin = user.is_staff or user.user_roles.filter(role__name='admin').exists()
        is_manager = supplier_request.manager_id == user.id
        is_supplier = hasattr(user, 'supplier_profile') and user.supplier_profile and \
                       user.supplier_profile.id == supplier_request.supplier_id
        
        if not (is_admin or is_manager or is_supplier):
            return Response(
                {'detail': 'У вас нет доступа к этой заявке.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        communications = RequestCommunication.objects.filter(request_id=request_id)
        serializer = RequestCommunicationSerializer(communications, many=True)
        return Response(serializer.data)


class MarkCommunicationAsReadView(APIView):
    """API view для отметки сообщения как прочитанного."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request: Any, communication_id: Any) -> Any:
        """Отметка сообщения как прочитанного."""
        communication = get_object_or_404(RequestCommunication, id=communication_id)
        user = request.user
        
        # Проверка доступа
        is_admin = user.is_staff or user.user_roles.filter(role__name='admin').exists()
        is_manager = communication.request.manager_id == user.id
        is_supplier = hasattr(user, 'supplier_profile') and user.supplier_profile and \
                       user.supplier_profile.id == communication.request.supplier_id
        
        if not (is_admin or is_manager or is_supplier):
            return Response(
                {'detail': 'У вас нет доступа к этому сообщению.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        communication.is_read = True
        communication.read_at = timezone.now()
        communication.save()
        
        return Response(
            {'detail': 'Сообщение помечено как прочитанное.'},
            status=status.HTTP_200_OK
        )


# ==================== Договоры поставщика ====================

class CreateSupplierContractView(APIView):
    """
    API view для создания договора с поставщиком.
    Доступно для админов и менеджеров (пользователей с назначенными заявками).
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request: Any) -> Any:
        """Создание договора с поставщиком."""
        user = request.user
        
        # Проверяем роль:
        # 1. is_staff = Django admin
        # 2. Роль 'admin' в UserRole
        # 3. Является менеджером каких-либо заявок (назначен в SupplierProductRequest)
        is_admin = user.is_staff or user.user_roles.filter(role__name='admin').exists()
        is_manager = SupplierProductRequest.objects.filter(manager_id=user.id).exists()
        
        if not (is_admin or is_manager):
            return Response(
                {'detail': 'У вас нет прав для создания договора. is_staff=' + str(user.is_staff) + ', roles=' + str(list(user.user_roles.values_list("role__name", flat=True)))},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Валидация данных
        required_fields = ['supplier', 'contract_number', 'title', 'start_date', 'end_date']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'detail': f'Поле {field} обязательно.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        supplier_id = request.data.get('supplier')
        supplier = get_object_or_404(Supplier, id=supplier_id)
        
        # Получаем или создаём статус договора
        status_id = request.data.get('status')
        if status_id:
            contract_status = get_object_or_404(ContractStatus, id=status_id)
        else:
            # Создаём статус по умолчанию, если его нет
            contract_status, _ = ContractStatus.objects.get_or_create(
                name='active',
                defaults={'description': 'Активный договор'}
            )
        
        # Проверяем, не существует ли уже такой договор
        existing_contract = SupplierContract.objects.filter(
            supplier=supplier,
            contract_number=request.data.get('contract_number')
        ).first()
        
        if existing_contract:
            return Response(
                {'detail': f"Договор с номером {request.data.get('contract_number')} для этого поставщика уже существует."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаём договор
        contract = SupplierContract.objects.create(
            supplier=supplier,
            status=contract_status,
            contract_number=request.data.get('contract_number'),
            title=request.data.get('title'),
            description=request.data.get('description', ''),
            start_date=request.data.get('start_date'),
            end_date=request.data.get('end_date'),
            total_amount=request.data.get('total_amount'),
            notes=request.data.get('notes', ''),
            is_auto_renew=request.data.get('is_auto_renew', False),
        )
        
        serializer = SupplierContractSerializer(contract)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MySupplierContractsView(APIView):
    """
    API view для получения договоров текущего поставщика.
    Поставщик видит только свои договоры.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Any) -> Any:
        """Получение договоров текущего поставщика."""
        user = request.user
        
        # Проверяем, что пользователь - поставщик
        if not hasattr(user, 'supplier_profile') or not user.supplier_profile:
            return Response(
                {'detail': 'Вы не являетесь поставщиком.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        supplier = user.supplier_profile
        contracts = SupplierContract.objects.filter(supplier=supplier).order_by('-created_at')
        serializer = SupplierContractSerializer(contracts, many=True)
        
        return Response(serializer.data)


class SupplierContractExpirationView(APIView):
    """
    API view для получения информации об истекающих договорах.
    Доступно для админов, менеджеров и поставщиков.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Any) -> Any:
        """Получение истекающих договоров."""
        from datetime import timedelta
        user = request.user
        
        # Определяем, какие договоры показывать
        is_admin = user.is_staff or user.user_roles.filter(role__name='admin').exists()
        is_manager = user.user_roles.filter(role__name='manager').exists()
        is_supplier = hasattr(user, 'supplier_profile') and user.supplier_profile
        
        # Получаем договоры, истекающие в течение 30 дней
        expiring_date = timezone.now().date() + timedelta(days=30)
        
        if is_supplier:
            # Поставщик видит только свои договоры
            contracts = SupplierContract.objects.filter(
                supplier=user.supplier_profile,
                end_date__gte=timezone.now().date(),
                end_date__lte=expiring_date
            ).order_by('end_date')
        elif is_admin or is_manager:
            # Админ и менеджер видят все договоры
            contracts = SupplierContract.objects.filter(
                end_date__gte=timezone.now().date(),
                end_date__lte=expiring_date
            ).order_by('end_date')
        else:
            return Response(
                {'detail': 'У вас нет доступа к этой информации.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = SupplierContractSerializer(contracts, many=True)
        
        # Дополнительная информация о количестве
        return Response({
            'count': len(serializer.data),
            'contracts': serializer.data,
            'days_until_expiration': 30
        })


class HandleExpiredContractsView(APIView):
    """
    API view для обработки истекших договоров.
    Деактивирует товары поставщиков, чьи договоры истекли.
    Только для админов.
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request: Any) -> Any:
        """Обработка истекших договоров."""
        from datetime import timedelta
        
        # Получаем истекшие договоры
        expired_contracts = SupplierContract.objects.filter(
            end_date__lt=timezone.now().date(),
            status__name='active'
        )
        
        results = []
        for contract in expired_contracts:
            # Меняем статус договора на истекший
            try:
                expired_status = ContractStatus.objects.get(name='expired')
                contract.status = expired_status
                contract.save(update_fields=['status', 'updated_at'])
            except ContractStatus.DoesNotExist:
                pass
            
            # Обрабатываем товары
            result = contract.handle_expiration()
            results.append(result)
            
            # Создаём уведомление для поставщика
            try:
                alert_type = AlertType.objects.get(name='contract_expired')
                SystemAlert.objects.create(
                    alert_type=alert_type,
                    user=contract.supplier.user,
                    title='Договор истёк',
                    message=f'Договор №{contract.contract_number} истёк. Связанные товары деактивированы.',
                    contract=contract
                )
            except (AlertType.DoesNotExist, AttributeError):
                pass  # Игнорируем если нет типа уведомления или пользователя
        
        return Response({
            'processed_contracts': len(results),
            'results': results
        })
