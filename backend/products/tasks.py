from typing import Any

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from products.models import Product


@shared_task
def check_low_stock_products(threshold: Any=5) -> Any:
    """Выполняет действие `check_low_stock_products`."""
    low_stock_products = Product.objects.filter(stock_quantity__lt=threshold, is_active=True)
    count = low_stock_products.count()

    if count > 0:
        product_lines = [f"- {p.name} (SKU: {p.sku}, остаток: {p.stock_quantity})" for p in low_stock_products[:50]]
        send_mail(
            subject='[OnlineStore] Товары с низким остатком',
            message='Найдены товары с низким остатком:\n' + '\n'.join(product_lines),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email for _, email in settings.ADMINS] if getattr(settings, 'ADMINS', None) else ['admin@localhost'],
            fail_silently=True,
        )

    return {
        'low_stock_count': count,
        'threshold': threshold,
    }
