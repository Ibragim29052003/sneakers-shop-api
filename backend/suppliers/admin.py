"""
Настройка админки для приложения поставщиков
"""
from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
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
from simple_history.admin import SimpleHistoryAdmin


@admin.register(Supplier)
class SupplierAdmin(SimpleHistoryAdmin):
    """Админка для модели поставщиков."""
    list_display = ('name', 'inn', 'phone', 'email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'inn', 'contact_person', 'email')
    date_hierarchy = 'created_at'
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)
    

@admin.register(SupplierContract)
class SupplierContractAdmin(SimpleHistoryAdmin):
    """Админка для модели договоров поставщиков."""
    list_display = ('contract_number', 'supplier', 'status', 'start_date', 'end_date', 'get_expiration_status')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('contract_number', 'supplier__name', 'title')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('supplier',)
    
    @display(description='Статус истечения')
    def get_expiration_status(self, obj):
        """Отображение статуса истечения договора."""
        if obj.is_expired:
            return mark_safe('<span style="color: red;">Истёк</span>')
        elif obj.is_expiring_soon:
            return mark_safe('<span style="color: orange;">Истекает скоро</span>')
        else:
            return mark_safe('<span style="color: green;">Активен</span>')


@admin.register(SupplierProductRequest)
class SupplierProductRequestAdmin(SimpleHistoryAdmin):
    """Админка для модели заявок на поставку товара."""
    list_display = ('product_name', 'supplier', 'status', 'manager', 'created_at', 'get_review_status')
    list_filter = ('status', 'created_at', 'supplier', 'manager')
    search_fields = ('product_name', 'product_sku', 'supplier__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('supplier', 'manager', 'reviewed_by')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at')
    
    @display(description='Статус проверки')
    def get_review_status(self, obj):
        """Отображение статуса проверки заявки."""
        if obj.reviewed_by:
            return format_html(
                '<span style="color: green;">Проверено {} {}</span>',
                obj.reviewed_by.first_name,
                obj.reviewed_by.last_name
            )
        return format_html('<span style="color: orange;">На проверке</span>')


@admin.register(ContractStatus)
class ContractStatusAdmin(SimpleHistoryAdmin):
    """Админка для модели статусов договоров."""
    list_display = ('name', 'description', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(RequestStatus)
class RequestStatusAdmin(SimpleHistoryAdmin):
    """Админка для модели статусов заявок."""
    list_display = ('name', 'description', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(DocumentType)
class DocumentTypeAdmin(SimpleHistoryAdmin):
    """Админка для модели типов документов."""
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(AlertType)
class AlertTypeAdmin(SimpleHistoryAdmin):
    """Админка для модели типов уведомлений."""
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(ProductSupplierSource)
class ProductSupplierSourceAdmin(SimpleHistoryAdmin):
    """Админка для модели источников товара."""
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(ContractDocument)
class ContractDocumentAdmin(SimpleHistoryAdmin):
    """Админка для модели документов договоров."""
    list_display = ('file_name', 'contract', 'document_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('file_name', 'contract__contract_number', 'uploaded_by__email')
    date_hierarchy = 'uploaded_at'
    raw_id_fields = ('contract', 'uploaded_by')


@admin.register(RequestDocument)
class RequestDocumentAdmin(SimpleHistoryAdmin):
    """Админка для модели документов заявок."""
    list_display = ('file_name', 'request', 'document_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('file_name', 'request__product_name', 'uploaded_by__email')
    date_hierarchy = 'uploaded_at'
    raw_id_fields = ('request', 'uploaded_by')


@admin.register(SupplierProduct)
class SupplierProductAdmin(SimpleHistoryAdmin):
    """Админка для модели поставок товаров."""
    list_display = ('product', 'supplier', 'supplier_sku', 'is_preferred', 'created_at')
    list_filter = ('is_preferred', 'created_at')
    search_fields = ('product__name', 'supplier__name', 'supplier_sku')
    date_hierarchy = 'created_at'
    raw_id_fields = ('product', 'supplier', 'contract')


@admin.register(SystemAlert)
class SystemAlertAdmin(SimpleHistoryAdmin):
    """Админка для модели системных уведомлений."""
    list_display = ('alert_type', 'title', 'is_read', 'created_at', 'get_read_status')
    list_filter = ('alert_type', 'is_read', 'created_at')
    search_fields = ('title', 'message')
    date_hierarchy = 'created_at'
    raw_id_fields = ('read_by', 'contract', 'request')
    
    @display(description='Статус прочтения')
    def get_read_status(self, obj):
        """Отображение статуса прочтения уведомления."""
        if obj.is_read:
            return format_html(
                '<span style="color: green;">Прочитано {}</span>',
                obj.read_at.strftime('%d.%m.%Y %H:%M') if obj.read_at else '-'
            )
        return format_html('<span style="color: orange;">Не прочитано</span>')
