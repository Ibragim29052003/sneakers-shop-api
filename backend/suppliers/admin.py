"""
Admin configuration для модуля управления поставщиками
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Supplier,
    SupplierContract,
    ContractStatus,
    DocumentType,
    ContractDocument,
    SupplierProductRequest,
    RequestStatus,
    RequestDocument,
    SupplierProduct,
    ProductSupplierSource,
    AlertType,
    SystemAlert,
)


# 
# СПРАВОЧНИКИ (READ-ONLY админка)
# 

@admin.register(ContractStatus)
class ContractStatusAdmin(admin.ModelAdmin):
    """Админка для статусов договоров"""
    list_display = ('id', 'name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    ordering = ('name',)
    
    # Поля только для чтения
    readonly_fields = ('id', 'created_at')


@admin.register(RequestStatus)
class RequestStatusAdmin(admin.ModelAdmin):
    """Админка для статусов заявок"""
    list_display = ('id', 'name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    ordering = ('name',)
    
    readonly_fields = ('id', 'created_at')


@admin.register(AlertType)
class AlertTypeAdmin(admin.ModelAdmin):
    """Админка для типов уведомлений"""
    list_display = ('id', 'name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    readonly_fields = ('id', 'created_at')


@admin.register(ProductSupplierSource)
class ProductSupplierSourceAdmin(admin.ModelAdmin):
    """Админка для источников создания товаров"""
    list_display = ('id', 'name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    readonly_fields = ('id', 'created_at')


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    """Админка для типов документов"""
    list_display = ('id', 'name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    readonly_fields = ('id', 'created_at')


# 
# ОСНОВНЫЕ МОДЕЛИ
# 

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Админка для поставщиков"""
    list_display = ('id', 'name', 'inn', 'phone', 'email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'inn', 'email', 'contact_person')
    list_editable = ('is_active',)
    ordering = ('name',)
    
    # Поля только для чтения
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    # Группировка полей
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'is_active')
        }),
        ('Реквизиты', {
            'fields': ('inn', 'kpp', 'ogrn', 'legal_address', 'actual_address')
        }),
        ('Контакты', {
            'fields': ('phone', 'email', 'website', 'contact_person', 'contact_phone')
        }),
        ('Дополнительно', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )


class ContractDocumentInline(admin.TabularInline):
    """Inline для документов договора"""
    model = ContractDocument
    extra = 1
    fields = ('document_type', 'file', 'file_name', 'description', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
    
    def has_delete_permission(self, request, obj=None):
        """Разрешаем удаление"""
        return True


@admin.register(SupplierContract)
class SupplierContractAdmin(admin.ModelAdmin):
    """Админка для договоров с поставщиками"""
    list_display = ('id', 'contract_number', 'supplier', 'status', 'start_date', 'end_date', 'total_amount', 'is_auto_renew')
    list_filter = ('status', 'is_auto_renew', 'start_date', 'end_date')
    search_fields = ('contract_number', 'title', 'supplier__name', 'description')
    ordering = ('-created_at',)
    
    # Поля только для чтения
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    # Inline документы
    inlines = [ContractDocumentInline]
    
    # Группировка полей
    fieldsets = (
        ('Основное', {
            'fields': ('supplier', 'status', 'contract_number', 'title')
        }),
        ('Сроки', {
            'fields': ('start_date', 'end_date', 'is_auto_renew')
        }),
        ('Финансы', {
            'fields': ('total_amount',)
        }),
        ('Дополнительно', {
            'fields': ('description', 'notes', 'created_at', 'updated_at')
        }),
    )
    
    # Автоматическое отображение даты окончания с цветовой индикацией
    @admin.display(description='дата окончания')
    def get_end_date_display(self, obj):
        from datetime import timedelta
        from django.utils import timezone
        
        if obj.end_date < timezone.now().date():
            return format_html(
                '<span style="color: red;">{}</span>',
                obj.end_date
            )
        elif obj.end_date <= timezone.now().date() + timedelta(days=30):
            return format_html(
                '<span style="color: orange;">{}</span>',
                obj.end_date
            )
        return obj.end_date


class RequestDocumentInline(admin.TabularInline):
    """Inline для документов заявки"""
    model = RequestDocument
    extra = 1
    fields = ('document_type', 'file', 'file_name', 'description', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(SupplierProductRequest)
class SupplierProductRequestAdmin(admin.ModelAdmin):
    """Админка для заявок на поставку"""
    list_display = ('id', 'product_name', 'supplier', 'status', 'quantity', 'suggested_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('product_name', 'product_sku', 'supplier__name', 'notes')
    ordering = ('-created_at',)
    
    # Поля только для чтения
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    # Inline документы
    inlines = [RequestDocumentInline]
    
    # Группировка полей
    fieldsets = (
        ('Основное', {
            'fields': ('supplier', 'status')
        }),
        ('Информация о товаре', {
            'fields': ('product_name', 'product_sku', 'product_description', 'quantity', 'suggested_price')
        }),
        ('Проверка', {
            'fields': ('reviewed_by', 'reviewed_at', 'review_comment')
        }),
        ('Дополнительно', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    
    # Автоматическое заполнение reviewed_at при изменении статуса
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            from django.utils import timezone
            obj.reviewed_at = timezone.now()
            if not obj.reviewed_by_id:
                obj.reviewed_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    """Админка для связи товаров и поставщиков"""
    list_display = ('id', 'product', 'supplier', 'supplier_sku', 'supplier_price', 'is_preferred', 'updated_at')
    list_filter = ('is_preferred',)
    search_fields = ('product__name', 'product__sku', 'supplier__name', 'supplier_sku')
    list_editable = ('is_preferred',)
    ordering = ('-is_preferred', 'supplier__name', 'product__name')
    
    # Поля только для чтения
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(SystemAlert)
class SystemAlertAdmin(admin.ModelAdmin):
    """Админка для системных уведомлений"""
    list_display = ('id', 'alert_type', 'title', 'is_read', 'contract', 'request', 'created_at')
    list_filter = ('alert_type', 'is_read', 'created_at')
    search_fields = ('title', 'message')
    list_editable = ('is_read',)
    ordering = ('-created_at',)
    
    # Поля только для чтения
    readonly_fields = ('id', 'created_at')
    
    # Группировка полей
    fieldsets = (
        ('Основное', {
            'fields': ('alert_type', 'title', 'message')
        }),
        ('Статус', {
            'fields': ('is_read', 'read_by', 'read_at')
        }),
        ('Связанные объекты', {
            'fields': ('contract', 'request')
        }),
        ('Служебное', {
            'fields': ('created_at',)
        }),
    )
    
    # Действия в админке
    actions = ['mark_as_read', 'mark_as_unread']
    
    @admin.action(description='Отметить как прочитанные')
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_read=True, read_by=request.user, read_at=timezone.now())
        self.message_user(request, f'Обновлено {updated} уведомлений.')
    
    @admin.action(description='Отметить как непрочитанные')
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_by=None, read_at=None)
        self.message_user(request, f'Обновлено {updated} уведомлений.')
