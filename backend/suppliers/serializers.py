"""
Сериализаторы для приложения поставщиков
"""
from rest_framework import serializers
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


class ContractStatusSerializer(serializers.ModelSerializer):
    """Сериализатор для модели статусов договоров."""
    
    class Meta:
        model = ContractStatus
        fields = ['id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class RequestStatusSerializer(serializers.ModelSerializer):
    """Сериализатор для модели статусов заявок."""
    
    class Meta:
        model = RequestStatus
        fields = ['id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class DocumentTypeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели типов документов."""
    
    class Meta:
        model = DocumentType
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['created_at']


class AlertTypeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели типов уведомлений."""
    
    class Meta:
        model = AlertType
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['created_at']


class ProductSupplierSourceSerializer(serializers.ModelSerializer):
    """Сериализатор для модели источников товара."""
    
    class Meta:
        model = ProductSupplierSource
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['created_at']


class SupplierSerializer(serializers.ModelSerializer):
    """Сериализатор для модели поставщиков."""
    contracts_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'inn', 'kpp', 'ogrn', 'legal_address', 'actual_address',
            'phone', 'email', 'website', 'contact_person', 'contact_phone',
            'notes', 'is_active', 'created_at', 'updated_at',
            'contracts_count', 'products_count'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_contracts_count(self, obj):
        return obj.contracts.count()
    
    def get_products_count(self, obj):
        return obj.products.count()


class SupplierContractSerializer(serializers.ModelSerializer):
    """Сериализатор для модели договоров поставщиков."""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)
    documents_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    is_expiring_soon = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = SupplierContract
        fields = [
            'id', 'supplier', 'supplier_name', 'status', 'status_name',
            'contract_number', 'title', 'description', 'start_date', 'end_date',
            'total_amount', 'notes', 'is_auto_renew', 'created_at', 'updated_at',
            'documents_count', 'products_count', 'is_expiring_soon', 'is_expired'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_documents_count(self, obj):
        return obj.documents.count()
    
    def get_products_count(self, obj):
        return obj.products.count()


class ContractDocumentSerializer(serializers.ModelSerializer):
    """Сериализатор для модели документов договоров."""
    uploaded_by_name = serializers.CharField(source='uploaded_by.email', read_only=True)
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)
    
    class Meta:
        model = ContractDocument
        fields = [
            'id', 'contract', 'document_type', 'document_type_name',
            'file', 'file_name', 'description', 'uploaded_at',
            'uploaded_by', 'uploaded_by_name'
        ]
        read_only_fields = ['uploaded_at']


class SupplierProductRequestSerializer(serializers.ModelSerializer):
    """Сериализатор для модели заявок на поставку товара."""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.email', read_only=True)
    manager_name = serializers.CharField(source='manager.email', read_only=True)
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SupplierProductRequest
        fields = [
            'id', 'supplier', 'supplier_name', 'status', 'status_name',
            'product_name', 'product_sku', 'product_description', 'quantity',
            'suggested_price', 'notes', 'reviewed_by', 'reviewed_by_name',
            'reviewed_at', 'review_comment', 'manager', 'manager_name',
            'created_at', 'updated_at', 'documents_count'
        ]
        read_only_fields = ['created_at', 'updated_at', 'reviewed_at']
    
    def get_documents_count(self, obj):
        return obj.documents.count()


class SupplierProductRequestCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания заявок на поставку товара."""
    
    class Meta:
        model = SupplierProductRequest
        fields = [
            'supplier', 'product_name', 'product_sku', 'product_description',
            'quantity', 'suggested_price', 'notes'
        ]


class SupplierProductRequestManageSerializer(serializers.ModelSerializer):
    """Сериализатор для управления заявками на поставку (одобрение/отклонение)."""
    
    class Meta:
        model = SupplierProductRequest
        fields = ['status', 'review_comment']


class RequestDocumentSerializer(serializers.ModelSerializer):
    """Сериализатор для модели документов заявок."""
    uploaded_by_name = serializers.CharField(source='uploaded_by.email', read_only=True)
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)
    
    class Meta:
        model = RequestDocument
        fields = [
            'id', 'request', 'document_type', 'document_type_name',
            'file', 'file_name', 'description', 'uploaded_at',
            'uploaded_by', 'uploaded_by_name'
        ]
        read_only_fields = ['uploaded_at']


class SupplierProductSerializer(serializers.ModelSerializer):
    """Сериализатор для модели поставок товаров."""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    
    class Meta:
        model = SupplierProduct
        fields = [
            'id', 'supplier', 'supplier_name', 'product', 'product_name',
            'contract', 'contract_number', 'supplier_sku', 'supplier_price',
            'is_preferred', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SystemAlertSerializer(serializers.ModelSerializer):
    """Сериализатор для модели системных уведомлений."""
    alert_type_name = serializers.CharField(source='alert_type.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    read_by_email = serializers.CharField(source='read_by.email', read_only=True)
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    request_info = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemAlert
        fields = [
            'id', 'alert_type', 'alert_type_name', 'user', 'user_email',
            'title', 'message', 'is_read', 'read_by', 'read_by_email',
            'read_at', 'contract', 'contract_number', 'request',
            'request_info', 'created_at'
        ]
        read_only_fields = ['created_at', 'read_at']
    
    def get_request_info(self, obj):
        if obj.request:
            return {
                'id': obj.request.id,
                'product_name': obj.request.product_name,
                'supplier_name': obj.request.supplier.name
            }
        return None


class SystemAlertCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания системных уведомлений."""
    
    class Meta:
        model = SystemAlert
        fields = ['alert_type', 'user', 'title', 'message', 'contract', 'request']
