from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from orders.models import Order, OrderItem, OrderStatus
from orders.tasks import cancel_unpaid_orders, recalculate_product_popularity, send_daily_sales_report
from products.models import Product


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TaskFunctionsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(email='task-user@test.com', password='testpass123')

        self.new_status = OrderStatus.objects.create(id=1, name='new')
        self.paid_status = OrderStatus.objects.create(name='paid')
        self.cancelled_status = OrderStatus.objects.create(name='cancelled', is_final=True)

        self.product = Product.objects.create(
            name='Task Product',
            description='demo',
            price=Decimal('1000.00'),
            stock_quantity=3,
            sku='TASK-SKU-1',
            status='active',
            is_active=True,
        )

    def test_check_cancel_unpaid_orders_returns_count(self):
        stale_order = Order.objects.create(
            user=self.user,
            status=self.new_status,
            total=Decimal('1000.00'),
            shipping_address='A',
            created_at=timezone.now() - timedelta(hours=30),
        )
        fresh_order = Order.objects.create(
            user=self.user,
            status=self.new_status,
            total=Decimal('1000.00'),
            shipping_address='B',
            created_at=timezone.now(),
        )

        result = cancel_unpaid_orders(hours=24)

        stale_order.refresh_from_db()
        fresh_order.refresh_from_db()
        self.assertEqual(result['cancelled_orders'], 1)
        self.assertEqual(stale_order.status.name, 'cancelled')
        self.assertEqual(fresh_order.status.name, 'new')

    def test_send_daily_sales_report_returns_sales_amount(self):
        Order.objects.create(
            user=self.user,
            status=self.paid_status,
            total=Decimal('1500.00'),
            shipping_address='A',
        )
        result = send_daily_sales_report()
        self.assertEqual(result['paid_orders_count'], 1)
        self.assertEqual(result['sales_amount'], 1500.0)

    def test_recalculate_product_popularity_returns_count(self):
        order = Order.objects.create(user=self.user, status=self.paid_status, total=Decimal('1000.00'), shipping_address='A')
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            product_sku=self.product.sku,
            quantity=1,
            price=self.product.price,
        )
        result = recalculate_product_popularity()
        self.assertEqual(result['recalculated_products'], 1)
