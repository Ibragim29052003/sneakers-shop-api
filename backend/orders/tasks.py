from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Sum
from django.utils import timezone

from .models import Order, OrderStatus


@shared_task
def cancel_unpaid_orders(hours=24):
    cutoff = timezone.now() - timedelta(hours=hours)
    cancel_status = OrderStatus.objects.filter(name__iexact='cancelled').first()
    if cancel_status is None:
        return {'cancelled_orders': 0, 'reason': 'status_cancelled_not_found'}

    unpaid_orders = Order.objects.exclude(status__is_final=True).filter(created_at__lt=cutoff).exclude(
        status__name__in=['paid', 'delivered', 'completed', 'cancelled']
    )
    updated_count = unpaid_orders.update(status=cancel_status, updated_at=timezone.now())

    return {
        'cancelled_orders': updated_count,
        'hours_threshold': hours,
    }


@shared_task
def send_daily_sales_report():
    today = timezone.localdate()
    start_dt = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end_dt = timezone.make_aware(datetime.combine(today, datetime.max.time()))

    paid_statuses = ['paid', 'delivered', 'completed']
    qs = Order.objects.filter(status__name__in=paid_statuses, created_at__range=(start_dt, end_dt))
    total_sales = qs.aggregate(total=Sum('total'))['total'] or 0

    send_mail(
        subject='[OnlineStore] Ежедневный отчёт по продажам',
        message=f'Дата: {today}\nКоличество оплаченных заказов: {qs.count()}\nСумма продаж: {total_sales}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email for _, email in settings.ADMINS] if getattr(settings, 'ADMINS', None) else ['admin@localhost'],
        fail_silently=True,
    )

    return {
        'sales_amount': float(total_sales),
        'paid_orders_count': qs.count(),
        'date': str(today),
    }


@shared_task
def send_order_created_email(order_id):
    order = Order.objects.select_related('user').get(id=order_id)
    send_mail(
        subject=f'Ваш заказ #{order.id} создан',
        message=f'Спасибо за заказ! Номер: {order.id}. Сумма: {order.total}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        fail_silently=True,
    )
    return {'order_id': order.id, 'email': order.user.email}


@shared_task
def send_order_status_changed_email(order_id):
    order = Order.objects.select_related('user', 'status').get(id=order_id)
    send_mail(
        subject=f'Обновлён статус заказа #{order.id}',
        message=f'Новый статус вашего заказа: {order.status.name}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        fail_silently=True,
    )
    return {'order_id': order.id, 'status': order.status.name}


@shared_task
def recalculate_product_popularity():
    # Заглушка под периодический пересчёт метрик популярности
    products_count = Order.objects.values('items__product').distinct().count()
    return {'recalculated_products': products_count}
