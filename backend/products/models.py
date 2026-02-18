"""
модели приложения товаров
"""
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from django.contrib.admin import display
from django.urls import reverse
from simple_history.models import HistoricalRecords
from datetime import timedelta


class ProductManager(models.Manager):
    """
    Кастомный менеджер модели товара
    Позволяет выполнять расширенные запросы к товарам
    """
    
    def active(self):
        """Возвращает только активные товары"""
        return self.filter(is_active=True)
    
    def with_price_range(self, min_price=None, max_price=None):
        """Фильтрует товары по диапазону цен"""
        queryset = self.all()
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        return queryset
    
    def recently_created(self, days=7):
        """Возвращает товары, созданные за последние N дней"""
        from django.utils import timezone
        start_date = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=start_date)
    
    def low_stock(self, threshold=10):
        """Возвращает товары с низким запасом (требует связи с Inventory)"""
        # Пример использования через связанную таблицу
        return self.filter(inventory__quantity__lt=threshold)
    
    def without_category(self):
        """Возвращает товары без категории"""
        return self.filter(categories__isnull=True)
    
    def created_by_supplier(self, supplier_id):
        """Возвращает товары конкретного поставщика"""
        return self.filter(supplier_id=supplier_id)


class Category(models.Model):
    # модель категории с иерархической структурой
    name = models.CharField('название категории', max_length=100)
    description = models.TextField('описание', blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name='родительская категория'
    )
    is_active = models.BooleanField('активна', default=True)
    created_at = models.DateTimeField('дата создания', default=timezone.now)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)
    
    # отслеживание истории изменений через simple_history
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @display(description='полный путь')
    def get_full_path(self):
        # получение полного пути категории включая родителей
        if self.parent:
            return f'{self.parent.get_full_path()} > {self.name}'
        return self.name


class ProductCategory(models.Model):
    """
    Промежуточная модель для связи товаров и категорий (M2M).
    
    ПРИМЕР ИСПОЛЬЗОВАНИЯ ManyToManyField с through:
    
    through параметр позволяет создать промежуточную модель с дополнительными полями.
    В данном случае мы храним дату добавления товара в категорию (created_at).
    
    БЕЗ through (простая M2M связь):
    - Только связи product_id и category_id
    - Нельзя добавить дополнительные данные
    
    С through (данная реализация):
    - Можно хранить дату добавления
    - Можно добавить другие поля (например, порядок, приоритет)
    - Можно добавить методы и логику к связи
    
    ПРИМЕР ИСПОЛЬЗОВАНИЯ:
    product = Product.objects.get(pk=1)
    category = Category.objects.get(pk=1)
    
    # Добавление товара в категорию
    ProductCategory.objects.create(product=product, category=category)
    
    # Или через add() метод
    product.categories.add(category)  # автоматически создаёт ProductCategory
    
    # Получение всех связей товара
    product.product_categories.all()  # все связи товара с категориями
    category.category_products.all()   # все связи категории с товарами
    """
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='product_categories',
        verbose_name='товар'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='category_products',
        verbose_name='категория'
    )
    created_at = models.DateTimeField('дата добавления', default=timezone.now)
    
    class Meta:
        verbose_name = 'связь товара и категории'
        verbose_name_plural = 'связи товаров и категорий'
        unique_together = ('product', 'category')
    
    def __str__(self):
        return f'{self.product.name} - {self.category.name}'


class ProductImage(models.Model):
    # модель изображений товара
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='товар'
    )
    image = models.ImageField('изображение', upload_to='products/%Y/%m/%d')
    is_main = models.BooleanField('основное изображение', default=False)
    alt_text = models.CharField('альтернативный текст', max_length=200, blank=True)
    created_at = models.DateTimeField('дата добавления', default=timezone.now)
    
    class Meta:
        verbose_name = 'изображение товара'
        verbose_name_plural = 'изображения товаров'
        ordering = ['-is_main', 'created_at']
    
    def __str__(self):
        return f'{self.product.name} - {self.id}'
    
    @display(description='превью')
    def image_preview(self):
        # отображение превью изображения в админке
        if self.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: auto;" />',
                self.image.url
            )
        return ''


class SliderImage(models.Model):
    """
    Модель для изображений слайдера на главной странице.
    Отдельная таблица от товаров - слайды заполняются и редактируются отдельно.
    """
    title = models.CharField('заголовок слайда', max_length=200)
    description = models.TextField('описание', blank=True)
    image = models.ImageField('изображение слайдера', upload_to='slider/%Y/%m/%d')
    product = models.ForeignKey(
        'Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='slider_images',
        verbose_name='связанный товар'
    )
    price = models.DecimalField(
        'цена',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Цена товара на слайде. Если указан товар, используется цена товара.'
    )
    old_price = models.DecimalField(
        'старая цена',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Старая цена для отображения скидки'
    )
    link = models.URLField('ссылка', blank=True, help_text='Ссылка при нажатии на слайд')
    is_active = models.BooleanField('активен', default=True)
    order = models.PositiveIntegerField('порядок', default=0)
    created_at = models.DateTimeField('дата добавления', default=timezone.now)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'слайд'
        verbose_name_plural = 'слайды'
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return self.title
    
    def get_image_url(self):
        """Получение полного URL изображения."""
        if self.image:
            return self.image.url
        return None
    
    @display(description='превью')
    def image_preview(self):
        if self.image:
            return format_html(
                '<img src="{}" style="width: 200px; height: auto;" />',
                self.image.url
            )
        return ''


class Product(models.Model):
    """
    Основная модель товара.
    
    ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ timezone:
    
    1. Пример: При создании товара сохраняется дата создания (created_at).
       Это дата, когда товар был добавлен в систему.
       Используется для:
       - Сортировки товаров по новизне
    - Фильтрации товаров за последние N дней
    - Отображения "новых поступлений" на сайте
    
    2. Пример: Расчёт скидки в зависимости от срока хранения на складе.
       Если товар хранится более 30 дней, применяется скидка:
       - 30+ дней: скидка 5%
    - 60+ дней: скидка 10%
    - 90+ дней: скидка 20%
    
    3. Пример: Определение "свежести" товара для маркетплейса.
       Товары менее 7 дней считаются "новыми", отображаются в разделе "Новинки".
    """
    
    # Статусы товара для демонстрации choices
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('active', 'Активен'),
        ('archived', 'В архиве'),
        ('out_of_stock', 'Нет в наличии'),
    ]
    
    # Кастомный менеджер
    objects = ProductManager()
    
    name = models.CharField('название товара', max_length=200)
    description = models.TextField('описание', blank=True)
    price = models.DecimalField('цена', max_digits=10, decimal_places=2)
    sku = models.CharField('артикул', max_length=50, unique=True)
    status = models.CharField(
        'статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_active = models.BooleanField('активен', default=True)
    created_at = models.DateTimeField('дата создания', default=timezone.now)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)
    
    # Поле для демонстрации расчёта скидки на основе срока хранения
    warehouse_date = models.DateField(
        'дата поступления на склад',
        null=True,
        blank=True,
        help_text='Дата когда товар поступил на склад. Используется для расчёта скидки.'
    )
    
    # связи с поставщиками (nullable - расширение существующей модели)
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='поставщик'
    )
    contract = models.ForeignKey(
        'suppliers.SupplierContract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='договор поставки'
    )
    created_from_request = models.ForeignKey(
        'suppliers.SupplierProductRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_products',
        verbose_name='создан из заявки'
    )
    created_from_source = models.ForeignKey(
        'suppliers.ProductSupplierSource',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='источник создания'
    )
    
    # Связь с категориями
    # ПРИМЕР ИСПОЛЬЗОВАНИЯ ManyToManyField с through параметром:
    #
    # through=ProductCategory указывает на промежуточную модель
    # Это позволяет хранить дополнительные данные о связи (дату добавления)
    #
    # Через related_name='products' можно обращаться:
    # - category.products.all() - все товары в категории
    # - product.categories.all() - все категории товара
    #
    # используем related_name вместо direct ManyToMany для совместимости с ProductCategory
    categories = models.ManyToManyField(
        Category,
        through=ProductCategory,
        related_name='products',
        verbose_name='категории'
    )
    
    # =========================================================================
    # ПРИМЕР ИСПОЛЬЗОВАНИЯ models.URLField()
    # =========================================================================
    # URLField - поле для хранения URL-адресов
    # max_length=200 - максимальная длина URL
    # blank=True - поле может быть пустым (необязательное)
    # verify_exists=False - не проверять существование URL (для производительности)
    #
    # ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:
    # product = Product.objects.get(pk=1)
    # product.external_url = 'https://example.com/product/123'
    # product.save()
    #
    # В админке/сериализаторе поле будет валидировать URL
    external_url = models.URLField(
        'внешняя ссылка',
        max_length=200,
        blank=True,
        null=True,
        help_text='Ссылка на товар на внешнем сайте'
    )
    
    # отслеживание истории изменений через simple_history
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_main_image(self):
        # получение основного изображения товара
        return self.images.filter(is_main=True).first()
    
    @display(description='цена')
    def get_price_with_currency(self):
        # отображение цены с символом валюты
        return f'{self.price} ₽'
    
    @display(description='категории')
    def get_categories_list(self):
        # получение списка названий категорий
        return ', '.join([c.name for c in self.categories.all()])
    
    def get_absolute_url(self):
        """
        Возвращает абсолютный URL для товара.
        Использует reverse() для генерации URL по имени маршрута.
        
        Пример использования в шаблоне:
        <a href="{{ product.get_absolute_url }}">{{ product.name }}</a>
        
        Пример использования в коде:
        product = Product.objects.get(pk=1)
        url = product.get_absolute_url()  # -> '/api/v1/products/1/'
        
        reverse() ищет маршрут по имени 'product-detail', который автоматически
        создаётся DRF Router при регистрации ViewSet с basename='product'.
        """
        return reverse('product-detail', kwargs={'pk': self.pk})
    
    def get_days_in_warehouse(self):
        """
        ПРИМЕР ИСПОЛЬЗОВАНИЯ timezone:
        
        Рассчитывает количество дней, которое товар хранится на складе.
        
        Returns:
            int: Количество дней на складе или 0 если дата не указана
        """
        if self.warehouse_date:
            # Используем timezone.now() для получения текущей даты с учётом временной зоны
            days = (timezone.now().date() - self.warehouse_date).days
            return max(0, days)  # Не возвращаем отрицательные значения
        return 0
    
    def get_discount_percentage(self):
        """
        ПРИМЕР ИСПОЛЬЗОВАНИЯ timezone:
        
        Рассчитывает процент скидки в зависимости от срока хранения на складе.
        
        Бизнес-логика:
        - Товар на складе менее 30 дней: скидка 0%
        - 30-59 дней: скидка 5%
        - 60-89 дней: скидка 10%
        - 90+ дней: скидка 20%
        
        Returns:
            int: Процент скидки (0-20)
        """
        days = self.get_days_in_warehouse()
        
        if days >= 90:
            return 20
        elif days >= 60:
            return 10
        elif days >= 30:
            return 5
        else:
            return 0
    
    def get_discounted_price(self):
        """
        ПРИМЕР ИСПОЛЬЗОВАНИЯ timezone:
        
        Рассчитывает цену со скидкой на основе срока хранения товара.
        
        Returns:
            Decimal: Цена со скидкой
        """
        from decimal import Decimal
        discount = Decimal(str(self.get_discount_percentage())) / 100
        return self.price * (Decimal('1') - discount)
    
    def is_new(self):
        """
        ПРИМЕР ИСПОЛЬЗОВАНИЯ timezone:
        
        Определяет, является ли товар "новым" (менее 7 дней с момента создания).
        
        Returns:
            bool: True если товар новый
        """
        days_since_creation = (timezone.now() - self.created_at).days
        return days_since_creation < 7
