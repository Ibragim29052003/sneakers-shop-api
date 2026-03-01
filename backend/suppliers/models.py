"""
Модели приложения управления поставщиками и договорами
"""
from django.db import models
from django.utils import timezone
from django.conf import settings
from simple_history.models import HistoricalRecords


def get_default_contract_status():
    """Получить статус договора по умолчанию"""
    from .models import ContractStatus
    return ContractStatus.objects.get(name=ContractStatus.DRAFT)


def get_default_request_status():
    """Получить статус заявки по умолчанию"""
    from .models import RequestStatus
    return RequestStatus.objects.get(name=RequestStatus.PENDING)


class ContractStatus(models.Model):
    """
    Статусы договоров с поставщиками
    """
    DRAFT = 'draft'
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    EXPIRED = 'expired'
    TERMINATED = 'terminated'

    STATUS_CHOICES = [
        (DRAFT, 'Черновик'),
        (ACTIVE, 'Активный'),
        (SUSPENDED, 'Приостановлен'),
        (EXPIRED, 'Истёк'),
        (TERMINATED, 'Расторгнут'),
    ]

    name = models.CharField(
        'название статуса',
        max_length=50,
        unique=True,
        choices=STATUS_CHOICES,
        default=DRAFT
    )
    description = models.TextField('описание', blank=True)
    is_active = models.BooleanField('активен', default=True)
    created_at = models.DateTimeField('дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'статус договора'
        verbose_name_plural = 'статусы договоров'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class RequestStatus(models.Model):
    """
    Статусы заявок на поставку товаров
    """
    PENDING = 'pending'
    UNDER_REVIEW = 'under_review'
    APPROVED = 'approved'
    REVISION_REQUIRED = 'revision_required'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (PENDING, 'Ожидает рассмотрения'),
        (UNDER_REVIEW, 'На рассмотрении'),
        (APPROVED, 'Одобрена'),
        (REVISION_REQUIRED, 'Требует доработки'),
        (REJECTED, 'Отклонена'),
    ]

    name = models.CharField(
        'название статуса',
        max_length=50,
        unique=True,
        choices=STATUS_CHOICES,
        default=PENDING
    )
    description = models.TextField('описание', blank=True)
    is_active = models.BooleanField('активен', default=True)
    created_at = models.DateTimeField('дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'статус заявки'
        verbose_name_plural = 'статусы заявок'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class AlertType(models.Model):
    """
    Типы системных уведомлений/алертов
    """
    CONTRACT_EXPIRING = 'contract_expiring'
    CONTRACT_EXPIRED = 'contract_expired'
    REQUEST_WAITING_REVIEW = 'request_waiting_review'

    TYPE_CHOICES = [
        (CONTRACT_EXPIRING, 'Договор истекает'),
        (CONTRACT_EXPIRED, 'Договор истёк'),
        (REQUEST_WAITING_REVIEW, 'Заявка ожидает рассмотрения'),
    ]

    name = models.CharField(
        'название типа',
        max_length=50,
        unique=True,
        choices=TYPE_CHOICES,
    )
    description = models.TextField('описание', blank=True)
    created_at = models.DateTimeField('дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'тип уведомления'
        verbose_name_plural = 'типы уведомлений'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class ProductSupplierSource(models.Model):
    """
    Источник создания товара (канал поставки)
    """
    MANUAL = 'manual'
    REQUEST = 'request'
    IMPORT = 'import'
    API = 'api'

    SOURCE_CHOICES = [
        (MANUAL, 'Ручное создание'),
        (REQUEST, 'Из заявки поставщика'),
        (IMPORT, 'Импорт'),
        (API, 'API'),
    ]

    name = models.CharField(
        'название источника',
        max_length=50,
        unique=True,
        choices=SOURCE_CHOICES,
    )
    description = models.TextField('описание', blank=True)
    created_at = models.DateTimeField('дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'источник товара'
        verbose_name_plural = 'источники товаров'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class DocumentType(models.Model):
    """
    Типы документов (договоры, акты, накладные и т.д.)
    """
    CONTRACT = 'contract'
    ACT = 'act'
    INVOICE = 'invoice'
    WAYBILL = 'waybill'
    CERTIFICATE = 'certificate'
    LICENSE = 'license'
    OTHER = 'other'

    TYPE_CHOICES = [
        (CONTRACT, 'Договор'),
        (ACT, 'Акт'),
        (INVOICE, 'Счёт/Инвойс'),
        (WAYBILL, 'Накладная'),
        (CERTIFICATE, 'Сертификат'),
        (LICENSE, 'Лицензия'),
        (OTHER, 'Другое'),
    ]

    name = models.CharField(
        'название типа',
        max_length=50,
        unique=True,
        choices=TYPE_CHOICES,
    )
    description = models.TextField('описание', blank=True)
    created_at = models.DateTimeField('дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'тип документа'
        verbose_name_plural = 'типы документов'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class Supplier(models.Model):
    """
    Модель поставщика
    """
    name = models.CharField('название поставщика', max_length=200)
    inn = models.CharField('ИНН', max_length=12, blank=True)
    kpp = models.CharField('КПП', max_length=9, blank=True)
    ogrn = models.CharField('ОГРН', max_length=15, blank=True)
    legal_address = models.TextField('юридический адрес', blank=True)
    actual_address = models.TextField('фактический адрес', blank=True)
    phone = models.CharField('телефон', max_length=20, blank=True)
    email = models.EmailField('email', blank=True)
    website = models.URLField('сайт', blank=True)
    contact_person = models.CharField('контактное лицо', max_length=100, blank=True)
    contact_phone = models.CharField('контактный телефон', max_length=20, blank=True)
    notes = models.TextField('заметки', blank=True)
    is_active = models.BooleanField('активен', default=True)
    
    # Связь с пользователем системы (если поставщик имеет аккаунт)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supplier_profile',
        verbose_name='аккаунт пользователя'
    )
    
    created_at = models.DateTimeField('дата создания', default=timezone.now)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)

    # отслеживание истории изменений
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'поставщик'
        verbose_name_plural = 'поставщики'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['inn']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class SupplierContract(models.Model):
    """
    Договор с поставщиком
    """
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='contracts',
        verbose_name='поставщик'
    )
    status = models.ForeignKey(
        ContractStatus,
        on_delete=models.PROTECT,
        related_name='Contracts',
        verbose_name='статус',
        default=get_default_contract_status
    )
    contract_number = models.CharField('номер договора', max_length=50)
    title = models.CharField('название договора', max_length=200)
    description = models.TextField('описание', blank=True)
    start_date = models.DateField('дата начала')
    end_date = models.DateField('дата окончания')
    total_amount = models.DecimalField(
        'сумма договора',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    notes = models.TextField('заметки', blank=True)
    is_auto_renew = models.BooleanField('автопродление', default=False)
    created_at = models.DateTimeField('дата создания', default=timezone.now)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)

    # отслеживание истории изменений
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'договор поставщика'
        verbose_name_plural = 'договоры поставщиков'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract_number']),
            models.Index(fields=['status']),
            models.Index(fields=['end_date']),
            models.Index(fields=['supplier', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['supplier', 'contract_number'],
                name='unique_contract_number_per_supplier'
            )
        ]

    def __str__(self):
        return f'{self.contract_number} - {self.supplier.name}'

    @property
    def is_expiring_soon(self):
        """Проверка, истекает ли договор в течение 30 дней"""
        from datetime import timedelta
        return self.end_date <= timezone.now().date() + timedelta(days=30)

    @property
    def is_expired(self):
        """Проверка, истёк ли договор"""
        return self.end_date < timezone.now().date()


class ContractDocument(models.Model):
    """
    Документы, прикреплённые к договору
    """
    contract = models.ForeignKey(
        SupplierContract,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='договор'
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        related_name='contract_documents',
        verbose_name='тип документа'
    )
    file = models.FileField('файл', upload_to='contracts/documents/%Y/%m/%d')
    file_name = models.CharField('название файла', max_length=255)
    description = models.TextField('описание', blank=True)
    uploaded_at = models.DateTimeField('дата загрузки', default=timezone.now)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_contract_documents',
        verbose_name='загрузил'
    )

    class Meta:
        verbose_name = 'документ договора'
        verbose_name_plural = 'документы договоров'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['contract', 'document_type']),
        ]

    def __str__(self):
        return f'{self.file_name} ({self.document_type.name})'


class SupplierProductRequest(models.Model):
    """
    Заявка на поставку товара от поставщика
    """
    # Категории для отображения товара
    CATEGORY_CHOICES = [
        ('women', 'Женщинам'),
        ('men', 'Мужчинам'),
        ('children', 'Детям'),
    ]
    
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='product_requests',
        verbose_name='поставщик'
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_requests',
        verbose_name='менеджер'
    )
    status = models.ForeignKey(
        RequestStatus,
        on_delete=models.PROTECT,
        related_name='requests',
        verbose_name='статус',
        default=get_default_request_status
    )
    # Категория для отображения товара (women/men/children)
    category = models.CharField(
        'категория',
        max_length=20,
        choices=CATEGORY_CHOICES,
        blank=True,
        help_text='Категория, на странице которой будет отображаться товар'
    )
    product_name = models.CharField('название товара', max_length=200)
    product_sku = models.CharField('артикул', max_length=50, blank=True)
    product_description = models.TextField('описание товара', blank=True)
    product_images = models.JSONField(
        'изображения товара',
        default=list,
        blank=True,
        help_text='Список URL загруженных изображений товара'
    )
    quantity = models.PositiveIntegerField('количество', default=1)
    suggested_price = models.DecimalField(
        'предложенная цена',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    suggested_old_price = models.DecimalField(
        'предложенная старая цена',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Старая цена товара, которую указывает поставщик'
    )
    notes = models.TextField('заметки', blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_requests',
        verbose_name='проверил'
    )
    reviewed_at = models.DateTimeField('дата проверки', null=True, blank=True)
    review_comment = models.TextField('комментарий проверки', blank=True)
    created_at = models.DateTimeField('дата создания', default=timezone.now)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)

    # отслеживание истории изменений
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'заявка на поставку'
        verbose_name_plural = 'заявки на поставку'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['supplier', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'Заявка #{self.id} - {self.product_name} ({self.supplier.name})'


class RequestDocument(models.Model):
    """
    Документы, прикреплённые к заявке на поставку
    """
    request = models.ForeignKey(
        SupplierProductRequest,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='заявка'
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        related_name='request_documents',
        verbose_name='тип документа'
    )
    file = models.FileField('файл', upload_to='requests/documents/%Y/%m/%d')
    file_name = models.CharField('название файла', max_length=255)
    description = models.TextField('описание', blank=True)
    uploaded_at = models.DateTimeField('дата загрузки', default=timezone.now)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_request_documents',
        verbose_name='загрузил'
    )

    class Meta:
        verbose_name = 'документ заявки'
        verbose_name_plural = 'документы заявок'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['request', 'document_type']),
        ]

    def __str__(self):
        return f'{self.file_name} ({self.document_type.name})'


class SupplierProduct(models.Model):
    """
    Связь товара с поставщиком (M2M)
    """
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='supplier_products',
        verbose_name='поставщик'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='product_suppliers',
        verbose_name='товар'
    )
    contract = models.ForeignKey(
        SupplierContract,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supplier_products',
        verbose_name='договор'
    )
    supplier_sku = models.CharField('артикул у поставщика', max_length=50, blank=True)
    supplier_price = models.DecimalField(
        'цена поставщика',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_preferred = models.BooleanField('предпочитаемый поставщик', default=False)
    notes = models.TextField('заметки', blank=True)
    created_at = models.DateTimeField('дата добавления', default=timezone.now)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'товар поставщика'
        verbose_name_plural = 'товары поставщиков'
        ordering = ['-is_preferred', 'supplier__name']
        indexes = [
            models.Index(fields=['supplier', 'product']),
            models.Index(fields=['product', 'is_preferred']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['supplier', 'product'],
                name='unique_supplier_product'
            )
        ]

    def __str__(self):
        return f'{self.product.name} - {self.supplier.name}'


class SystemAlert(models.Model):
    """
    Системные уведомления/алерты
    """
    alert_type = models.ForeignKey(
        AlertType,
        on_delete=models.PROTECT,
        related_name='alerts',
        verbose_name='тип уведомления'
    )
    title = models.CharField('заголовок', max_length=200)
    message = models.TextField('сообщение')
    is_read = models.BooleanField('прочитано', default=False)
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='read_alerts',
        verbose_name='прочитал'
    )
    read_at = models.DateTimeField('дата прочтения', null=True, blank=True)
    
    # Связь с договором (nullable - не все алерты связаны с договорами)
    contract = models.ForeignKey(
        SupplierContract,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name='договор'
    )
    
    # Связь с заявкой (nullable)
    request = models.ForeignKey(
        SupplierProductRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name='заявка'
    )
    
    created_at = models.DateTimeField('дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'системное уведомление'
        verbose_name_plural = 'системные уведомления'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'is_read']),
            models.Index(fields=['is_read', 'created_at']),
            models.Index(fields=['contract', 'is_read']),
        ]

    def __str__(self):
        return f'{self.alert_type.name} - {self.title}'


class RequestCommunication(models.Model):
    """
    Сообщения/коммуникация между менеджером и поставщиком по заявке.
    Позволяет обсуждать детали заявки, согласовывать цены, условия и т.д.
    """
    FROM_MANAGER = 'manager'
    FROM_SUPPLIER = 'supplier'
    
    DIRECTION_CHOICES = [
        (FROM_MANAGER, 'От менеджера'),
        (FROM_SUPPLIER, 'От поставщика'),
    ]
    
    request = models.ForeignKey(
        SupplierProductRequest,
        on_delete=models.CASCADE,
        related_name='communications',
        verbose_name='заявка'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_communications',
        verbose_name='отправитель'
    )
    direction = models.CharField(
        'направление',
        max_length=20,
        choices=DIRECTION_CHOICES,
        default=FROM_MANAGER
    )
    message = models.TextField('сообщение')
    is_read = models.BooleanField('прочитано', default=False)
    read_at = models.DateTimeField('дата прочтения', null=True, blank=True)
    created_at = models.DateTimeField('дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'коммуникация по заявке'
        verbose_name_plural = 'коммуникации по заявкам'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['request', 'created_at']),
            models.Index(fields=['direction']),
        ]

    def __str__(self):
        return f'Сообщение #{self.id} по заявке #{self.request_id}'
