"""
модели приложения товаров
"""
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from django.contrib.admin import display
from simple_history.models import HistoricalRecords


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
    # связь товаров и категорий (многие-ко-многим)
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


class Product(models.Model):
    # основная модель товара
    name = models.CharField('название товара', max_length=200)
    description = models.TextField('описание', blank=True)
    price = models.DecimalField('цена', max_digits=10, decimal_places=2)
    sku = models.CharField('артикул', max_length=50, unique=True)
    is_active = models.BooleanField('активен', default=True)
    created_at = models.DateTimeField('дата создания', default=timezone.now)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)
    
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
    
    # связь с категориями
    # используем related_name вместо direct ManyToMany для совместимости с ProductCategory
    categories = models.ManyToManyField(
        Category,
        through=ProductCategory,
        related_name='products',
        verbose_name='категории'
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
