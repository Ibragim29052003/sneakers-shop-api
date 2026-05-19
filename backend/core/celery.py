import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-low-stock-products-09-00': {
        'task': 'products.tasks.check_low_stock_products',
        'schedule': crontab(hour=9, minute=0),
    },
    'cancel-unpaid-orders-hourly': {
        'task': 'orders.tasks.cancel_unpaid_orders',
        'schedule': crontab(minute=0),
    },
    'send-daily-sales-report-20-00': {
        'task': 'orders.tasks.send_daily_sales_report',
        'schedule': crontab(hour=20, minute=0),
    },
    'recalculate-product-popularity-nightly': {
        'task': 'orders.tasks.recalculate_product_popularity',
        'schedule': crontab(hour=2, minute=0),
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
