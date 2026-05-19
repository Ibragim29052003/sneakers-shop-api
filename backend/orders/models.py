"""
модели приложения заказов
"""
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.admin import display
from decimal import Decimal
from simple_history.models import HistoricalRecords


class OrderStatus(models.Model):
    # справочник статусов заказа
    name = models.CharField('название статуса', max_length=50, unique=True)
    description = models.TextField('описание', blank=True)
    is_final = models.BooleanField('финальный статус', default=False)
    created_at = models.DateTimeField('дата создания', default=timezone.now)
    
    class Meta:
        verbose_name = 'статус заказа'
        verbose_name_plural = 'статусы заказов'
        ordering = ['created_at']
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Защита от рассинхронизации sequence при явном задании id."""
        if self.pk is None:
            last_id = OrderStatus.objects.order_by('-id').values_list('id', flat=True).first() or 0
            self.pk = last_id + 1
        return super().save(*args, **kwargs)


class Order(models.Model):
    # модель заказа покупателя
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='пользователь'
    )
    status = models.ForeignKey(
        OrderStatus,
        on_delete=models.SET_DEFAULT,
        default=1,
        related_name='orders',
        verbose_name='статус'
    )
    total = models.DecimalField(
        'общая сумма',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    shipping_address = models.TextField('адрес доставки', blank=True)
    notes = models.TextField('Примечания к заказу', blank=True)
    created_at = models.DateTimeField('дата создания', default=timezone.now)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)
    
    # отслеживание истории изменений через simple_history
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(total__gt=0),
                name='order_total_gt_0',
            ),
        ]
    
    def clean(self):
        super().clean()
        if self.total <= 0:
            raise ValidationError({'total': 'Сумма заказа должна быть больше 0.'})

    def __str__(self):
        return f'заказ #{self.id} - {self.user.email}'
    
    @display(description='статус')
    def get_status_display(self):
        # отображение статуса с цветовой индикацией
        from django.utils.html import format_html
        if self.status.is_final:
            return format_html(
                '<span style="color: green;">{}</span>',
                self.status.name
            )
        return format_html(
            '<span style="color: orange;">{}</span>',
            self.status.name
        )
    
    @display(description='сумма')
    def get_total_display(self):
        # отображение суммы с валютой
        return f'{self.total} ₽'
    
    @display(description='количество товаров')
    def get_items_count(self):
        # получение количества товаров в заказе
        return self.items.count()
    
    def calculate_total(self):
        """Расчёт общей суммы заказа."""
        total = sum(item.get_total_price() for item in self.items.all())
        self.total = total
        self.save(update_fields=['total', 'updated_at'])
        return self.total


class OrderItem(models.Model):
    # модель товара в заказе
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='заказ'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items',
        verbose_name='товар'
    )
    product_name = models.CharField('название товара (на момент заказа)', max_length=200)
    product_sku = models.CharField('артикул (на момент заказа)', max_length=50)
    quantity = models.PositiveIntegerField('количество', default=1)
    price = models.DecimalField('цена за единицу', max_digits=10, decimal_places=2)
    created_at = models.DateTimeField('дата добавления', default=timezone.now)
    
    # отслеживание истории изменений через simple_history
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'товар в заказе'
        verbose_name_plural = 'товары в заказе'
    
    def __str__(self):
        return f'{self.product_name} x {self.quantity}'
    
    def get_total_price(self):
        # расчёт общей стоимости позиции
        if self.price is not None:
            return self.price * self.quantity
        return Decimal('0.00')
    
    @display(description='сумма')
    def get_total_price_display(self):
        # отображение общей стоимости с валютой
        return f'{self.get_total_price()} ₽'
    
    def save(self, *args, **kwargs):
        # сохранение информации о товаре из связанной модели
        if self.product and not self.product_name:
            self.product_name = self.product.name
            self.product_sku = self.product.sku
            self.price = self.product.price
        super().save(*args, **kwargs)
