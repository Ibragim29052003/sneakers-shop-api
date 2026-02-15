"""
Views for suppliers app.
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
)


# ==================== Reference Data Views ====================

class ContractStatusViewSet(viewsets.ModelViewSet):
    """ViewSet for ContractStatus model."""
    queryset = ContractStatus.objects.all()
    serializer_class = ContractStatusSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class RequestStatusViewSet(viewsets.ModelViewSet):
    """ViewSet for RequestStatus model."""
    queryset = RequestStatus.objects.all()
    serializer_class = RequestStatusSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class DocumentTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for DocumentType model."""
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class AlertTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for AlertType model."""
    queryset = AlertType.objects.all()
    serializer_class = AlertTypeSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class ProductSupplierSourceViewSet(viewsets.ModelViewSet):
    """ViewSet for ProductSupplierSource model."""
    queryset = ProductSupplierSource.objects.all()
    serializer_class = ProductSupplierSourceSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


# ==================== Supplier Views ====================

class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet for Supplier model."""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'inn', 'contact_person', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


# ==================== Contract Views ====================

class SupplierContractViewSet(viewsets.ModelViewSet):
    """ViewSet for SupplierContract model."""
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
        # Filter by expiring soon
        expiring_soon = self.request.query_params.get('expiring_soon')
        if expiring_soon == 'true':
            from datetime import timedelta
            queryset = queryset.filter(
                end_date__gte=timezone.now().date(),
                end_date__lte=timezone.now().date() + timedelta(days=30)
            )
        return queryset


class ContractDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for ContractDocument model."""
    queryset = ContractDocument.objects.all()
    serializer_class = ContractDocumentSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['contract', 'document_type']
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


# ==================== Supplier Product Request Views ====================

class SupplierProductRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for SupplierProductRequest model."""
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
            # Check if user is admin or manager of this request
            return SupplierProductRequestManageSerializer
        return SupplierProductRequestSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [IsAuthenticated()]
        return [CanManageSupplierRequests()]
    
    def get_queryset(self):
        user = self.request.user
        # Admin sees all requests
        if user.is_staff or user.user_roles.filter(role__name='admin').exists():
            return SupplierProductRequest.objects.all()
        # Manager sees their assigned requests
        if hasattr(self, 'action') and self.action in ['list', 'retrieve']:
            return SupplierProductRequest.objects.filter(
                manager_id=user.id
            ) | SupplierProductRequest.objects.filter(supplier__contact_person=user.email)
        return SupplierProductRequest.objects.filter(manager_id=user.id)
    
    def perform_create(self, serializer):
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        """Update request - for managing (approve/reject) requests."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check permissions
        if not request.user.is_staff and not request.user.user_roles.filter(role__name='admin').exists():
            if instance.manager_id != request.user.id:
                return Response(
                    {'detail': 'Вы не являетесь менеджером этой заявки.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # If status is being changed to approved/rejected, set reviewed_by and reviewed_at
        if 'status' in request.data and instance.status.name not in ['approved', 'rejected']:
            instance.reviewed_by = request.user
            instance.reviewed_at = timezone.now()
            instance.save()
        
        self.perform_update(serializer)
        return Response(serializer.data)


class AssignManagerView(APIView):
    """API view for assigning manager to supplier product request."""
    permission_classes = [CanAssignManager]
    
    def post(self, request, request_id):
        """Assign a manager to a supplier product request."""
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
        
        # Create notification for manager
        SystemAlert.objects.create(
            alert_type=AlertType.objects.get(name='request_waiting_review'),
            user=manager,
            title='Назначен менеджером заявки',
            message=f'Вы назначены менеджером заявки #{supplier_request.id} на товар "{supplier_request.product_name}"',
            request=supplier_request
        )
        
        return Response(
            {'detail': f'Менеджер {manager.email} назначен для заявки #{supplier_request.id}'},
            status=status.HTTP_200_OK
        )


class RequestDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for RequestDocument model."""
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


# ==================== Supplier Product Views ====================

class SupplierProductViewSet(viewsets.ModelViewSet):
    """ViewSet for SupplierProduct model."""
    queryset = SupplierProduct.objects.all()
    serializer_class = SupplierProductSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'product', 'is_preferred']
    search_fields = ['supplier__name', 'product__name', 'supplier_sku']
    ordering_fields = ['created_at', 'supplier__name']
    ordering = ['-is_preferred', 'supplier__name']


# ==================== System Alert Views ====================

class SystemAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for SystemAlert model."""
    queryset = SystemAlert.objects.all()
    serializer_class = SystemAlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['alert_type', 'is_read']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        # Admin sees all alerts
        if user.is_staff or user.user_roles.filter(role__name='admin').exists():
            return SystemAlert.objects.all()
        # Regular users see only their alerts
        return SystemAlert.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SystemAlertCreateSerializer
        return SystemAlertSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        """Mark alert as read."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if user owns this alert or is admin
        if instance.user != request.user:
            if not (request.user.is_staff or request.user.user_roles.filter(role__name='admin').exists()):
                return Response(
                    {'detail': 'Вы не можете изменять чужие уведомления.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # If marking as read, set read_by and read_at
        if 'is_read' in request.data and request.data['is_read'] and not instance.is_read:
            instance.read_by = request.user
            instance.read_at = timezone.now()
            instance.save()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def mark_as_read(self, request, pk=None):
        """Mark specific alert as read."""
        alert = get_object_or_404(SystemAlert, id=pk, user=request.user)
        alert.is_read = True
        alert.read_by = request.user
        alert.read_at = timezone.now()
        alert.save()
        return Response({'detail': 'Уведомление помечено как прочитанное.'})


class UserAlertsView(APIView):
    """API view for getting current user's alerts."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's alerts."""
        alerts = SystemAlert.objects.filter(user=request.user)
        unread_count = alerts.filter(is_read=False).count()
        serializer = SystemAlertSerializer(alerts, many=True)
        return Response({
            'count': alerts.count(),
            'unread_count': unread_count,
            'alerts': serializer.data
        })
    
    def post(self, request):
        """Mark all alerts as read."""
        SystemAlert.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_by=request.user,
            read_at=timezone.now()
        )
        return Response({'detail': 'Все уведомления помечены как прочитанные.'})
