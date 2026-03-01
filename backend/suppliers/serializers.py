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
    RequestCommunication,
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
    user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)
    contracts_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'inn', 'kpp', 'ogrn', 'legal_address', 'actual_address',
            'phone', 'email', 'website', 'contact_person', 'contact_phone',
            'notes', 'is_active', 'user', 'user_email', 'created_at', 'updated_at',
            'contracts_count', 'products_count'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_contracts_count(self, obj):
        return obj.contracts.count()
    
    def get_products_count(self, obj):
        return obj.products.count()


class SupplierRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации поставщика (создание от имени пользователя)."""
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Supplier
        fields = [
            'name', 'inn', 'kpp', 'ogrn', 'legal_address', 'actual_address',
            'phone', 'email', 'website', 'contact_person', 'contact_phone',
            'password', 'notes'
        ]
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Создаём пользователя если передан пароль
        user = None
        if password:
            email = validated_data.get('email')
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=validated_data.get('contact_person', '').split()[0] if validated_data.get('contact_person') else '',
                last_name=' '.join(validated_data.get('contact_person', '').split()[1:]) if validated_data.get('contact_person') else ''
            )
            # Назначаем роль поставщика
            from users.models import Role, UserRole
            supplier_role, _ = Role.objects.get_or_create(
                name='supplier',
                defaults={'description': 'Поставщик товаров'}
            )
            UserRole.objects.get_or_create(user=user, role=supplier_role)
        
        supplier = Supplier.objects.create(
            user=user,
            **validated_data
        )
        return supplier


class SupplierApplySerializer(serializers.ModelSerializer):
    """Сериализатор для заявки на регистрацию поставщика от существующего пользователя."""
    
    class Meta:
        model = Supplier
        fields = [
            'name', 'inn', 'kpp', 'ogrn', 'legal_address', 'actual_address',
            'phone', 'email', 'website', 'contact_person', 'contact_phone', 'notes'
        ]


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
            'category', 'product_name', 'product_sku', 'product_description',
            'product_images', 'quantity', 'suggested_price', 'suggested_old_price', 'notes',
            'reviewed_by', 'reviewed_by_name', 'reviewed_at', 'review_comment',
            'manager', 'manager_name', 'created_at', 'updated_at', 'documents_count'
        ]
        read_only_fields = ['created_at', 'updated_at', 'reviewed_at']
    
    def get_documents_count(self, obj):
        return obj.documents.count()


class SupplierProductRequestCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания заявок на поставку товара."""
    
    class Meta:
        model = SupplierProductRequest
        fields = [
            'supplier', 'category', 'product_name', 'product_sku', 'product_description',
            'product_images', 'quantity', 'suggested_price', 'suggested_old_price', 'notes'
        ]


class SupplierProductRequestManageSerializer(serializers.ModelSerializer):
    """Сериализатор для управления заявками на поставку (одобрение/отклонение)."""
    
    class Meta:
        model = SupplierProductRequest
        fields = ['status', 'review_comment', 'manager']


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


class SupplierWithRequestSerializer(serializers.Serializer):
    """
    Сериализатор для регистрации поставщика с заявкой на товар.
    Упрощённый workflow: одна форма = регистрация компании + предложение товара.
    """
    # Данные компании
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    contact_person = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    inn = serializers.CharField(max_length=12, required=False, allow_blank=True)
    kpp = serializers.CharField(max_length=9, required=False, allow_blank=True)
    ogrn = serializers.CharField(max_length=15, required=False, allow_blank=True)
    legal_address = serializers.CharField(required=False, allow_blank=True)
    actual_address = serializers.CharField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    # Данные товара
    product_name = serializers.CharField(max_length=200)
    product_sku = serializers.CharField(max_length=50, required=False, allow_blank=True)
    product_description = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.IntegerField(default=1, min_value=1)
    suggested_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    product_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_email(self, value):
        """Проверка, что email ещё не используется."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует. Используйте другой email или войдите в систему.")
        return value
    
    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        from users.models import Role, UserRole
        
        User = get_user_model()
        
        # Извлекаем данные товара
        product_name = validated_data.pop('product_name')
        product_sku = validated_data.pop('product_sku', '')
        product_description = validated_data.pop('product_description', '')
        quantity = validated_data.pop('quantity', 1)
        suggested_price = validated_data.pop('suggested_price', None)
        product_notes = validated_data.pop('product_notes', '')
        
        # Создаём пользователя
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=validated_data.get('contact_person', '').split()[0] if validated_data.get('contact_person') else '',
            last_name=' '.join(validated_data.get('contact_person', '').split()[1:]) if validated_data.get('contact_person') else ''
        )
        
        # Назначаем роль поставщика
        supplier_role, _ = Role.objects.get_or_create(
            name='supplier',
            defaults={'description': 'Поставщик товаров'}
        )
        UserRole.objects.get_or_create(user=user, role=supplier_role)
        
        # Создаём поставщика
        supplier = Supplier.objects.create(
            user=user,
            **validated_data
        )
        
        # Создаём заявку на товар
        from .models import SupplierProductRequest, RequestStatus
        pending_status = RequestStatus.objects.get(name=RequestStatus.PENDING)
        
        product_request = SupplierProductRequest.objects.create(
            supplier=supplier,
            status=pending_status,
            product_name=product_name,
            product_sku=product_sku,
            product_description=product_description,
            quantity=quantity,
            suggested_price=suggested_price,
            notes=product_notes
        )
        
        return {
            'supplier': supplier,
            'product_request': product_request
        }


class RequestCommunicationSerializer(serializers.ModelSerializer):
    """Сериализатор для коммуникации по заявке."""
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    request_info = serializers.SerializerMethodField()
    
    class Meta:
        model = RequestCommunication
        fields = [
            'id', 'request', 'request_info', 'sender', 'sender_email',
            'direction', 'message', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['created_at', 'read_at']
    
    def get_request_info(self, obj):
        return {
            'id': obj.request.id,
            'product_name': obj.request.product_name,
            'supplier_name': obj.request.supplier.name,
            'status': obj.request.status.name
        }


class RequestCommunicationCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания сообщения в коммуникации."""
    
    class Meta:
        model = RequestCommunication
        fields = ['request', 'message']
