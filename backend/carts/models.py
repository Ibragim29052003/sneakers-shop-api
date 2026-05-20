"""
модели приложения корзины
"""
from typing import Any

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.admin import display
from simple_history.models import HistoricalRecords


class Cart(models.Model):
    # модель корзины покупок
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='пользователь'
    )
    created_at = models.DateTimeField('дата создания', default=timezone.now)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)
    
    # отслеживание истории изменений через simple_history
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'корзина'
        verbose_name_plural = 'корзины'
    
    def __str__(self) -> Any:
        """Выполняет действие `__str__`."""
        return f'корзина пользователя {self.user.email}'
    
    @display(description='количество товаров')
    def get_total_items(self) -> Any:
        # получение общего количества товаров в корзине
        """Возвращает данные через `get_total_items`."""
        return self.items.count()
    
    @display(description='общая сумма')
    def get_total_price(self) -> Any:
        # получение общей суммы товаров в корзине
        """Возвращает данные через `get_total_price`."""
        total = sum(item.get_total_price() for item in self.items.all())
        return total
    
    @display(description='общая сумма')
    def get_total_price_display(self) -> Any:
        # отображение общей суммы с валютой
        """Возвращает данные через `get_total_price_display`."""
        return f'{self.get_total_price()} ₽'


class CartItem(models.Model):
    # модель товара в корзине
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='корзина'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='товар'
    )
    quantity = models.PositiveIntegerField(
        'количество',
        default=1,
        validators=[MinValueValidator(1)]
    )
    created_at = models.DateTimeField('дата добавления', default=timezone.now)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)
    
    # отслеживание истории изменений через simple_history
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'товар в корзине'
        verbose_name_plural = 'товары в корзине'
        unique_together = ('cart', 'product')
    
    def __str__(self) -> Any:
        """Выполняет действие `__str__`."""
        return f'{self.product.name} x {self.quantity}'
    
    def get_total_price(self) -> Any:
        # расчёт общей стоимости позиции
        """Возвращает данные через `get_total_price`."""
        return self.product.price * self.quantity
    
    @display(description='сумма')
    def get_total_price_display(self) -> Any:
        # отображение общей стоимости с валютой
        """Возвращает данные через `get_total_price_display`."""
        return f'{self.get_total_price()} ₽'
    
    @display(description='цена за шт.')
    def get_product_price(self) -> Any:
        # получение цены за единицу товара
        """Возвращает данные через `get_product_price`."""
        return self.product.price
