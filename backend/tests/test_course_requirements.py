from typing import Any

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from carts.models import Cart, CartItem
from orders.models import Order, OrderItem, OrderStatus
from products.models import Category, FilterGroup, FilterOption, Product, ProductFavorite, ProductFilter
from suppliers.models import Supplier
from reviews.models import Review
from users.models import Role, UserRole


class CourseRequirementsAPITests(TestCase):
    def setUp(self) -> Any:
        """Выполняет действие `setUp`."""
        self.client = APIClient()
        self.user_model = get_user_model()

        self.role_user = Role.objects.create(name='user')
        self.role_admin = Role.objects.create(name='admin')

        self.buyer = self.user_model.objects.create_user(email='buyer@test.com', password='testpass123')
        self.other_user = self.user_model.objects.create_user(email='other@test.com', password='testpass123')
        self.admin = self.user_model.objects.create_user(
            email='admin@test.com', password='testpass123', is_staff=True
        )

        UserRole.objects.create(user=self.buyer, role=self.role_user)
        UserRole.objects.create(user=self.other_user, role=self.role_user)
        UserRole.objects.create(user=self.admin, role=self.role_admin)

        self.order_status = OrderStatus.objects.create(id=1, name='new', description='new')
        self.paid_status = OrderStatus.objects.create(name='paid', description='paid')
        self.delivered_status = OrderStatus.objects.create(name='delivered', description='delivered', is_final=True)
        self.completed_status = OrderStatus.objects.create(name='completed', description='completed', is_final=True)
        self.cancelled_status = OrderStatus.objects.create(name='cancelled', description='cancelled', is_final=True)

        self.product_ok = Product.objects.create(
            name='Sneaker A',
            description='A',
            price=Decimal('600.00'),
            stock_quantity=10,
            sku='SKU-A',
            status='active',
            is_active=True,
        )
        self.product_low = Product.objects.create(
            name='Sneaker B',
            description='B',
            price=Decimal('400.00'),
            stock_quantity=2,
            sku='SKU-B',
            status='active',
            is_active=True,
        )
        self.product_oos = Product.objects.create(
            name='Sneaker C',
            description='C',
            price=Decimal('700.00'),
            stock_quantity=0,
            sku='SKU-C',
            status='out_of_stock',
            is_active=False,
        )
        self.product_archived = Product.objects.create(
            name='Sneaker D',
            description='D',
            price=Decimal('650.00'),
            stock_quantity=5,
            sku='SKU-D',
            status='archived',
            is_active=False,
        )
        self.product_draft = Product.objects.create(
            name='Sneaker E',
            description='E',
            price=Decimal('550.00'),
            stock_quantity=5,
            sku='SKU-E',
            status='draft',
            is_active=False,
        )

        self.category = Category.objects.create(name='Sneakers')
        self.discount_allowed_category = Category.objects.create(name='Women Sneakers')
        self.discount_forbidden_category = Category.objects.create(name='Accessories')
        self.product_ok.categories.add(self.category)

        self.supplier = Supplier.objects.create(name='ACME Supplier')
        self.product_ok.supplier = self.supplier
        self.product_ok.save(update_fields=['supplier'])

        self.color_group = FilterGroup.objects.create(name='Цвет', category=self.category)
        self.size_group = FilterGroup.objects.create(name='Размер', category=self.category)
        self.fabric_group = FilterGroup.objects.create(name='Материал', category=self.category)
        self.color_black = FilterOption.objects.create(group=self.color_group, name='black')
        self.color_white = FilterOption.objects.create(group=self.color_group, name='white')
        self.size_42 = FilterOption.objects.create(group=self.size_group, name='42')
        self.size_43 = FilterOption.objects.create(group=self.size_group, name='43')
        self.fabric_cotton = FilterOption.objects.create(group=self.fabric_group, name='cotton')

        ProductFilter.objects.create(product=self.product_ok, filter_option=self.color_black)
        ProductFilter.objects.create(product=self.product_ok, filter_option=self.size_42)
        ProductFilter.objects.create(product=self.product_ok, filter_option=self.fabric_cotton)

        Cart.objects.get_or_create(user=self.buyer)
        Cart.objects.get_or_create(user=self.other_user)

    def auth(self, user: Any) -> Any:
        """Выполняет действие `auth`."""
        self.client.force_authenticate(user=user)

    def _items(self, response: Any) -> Any:
        """Выполняет действие `_items`."""
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data

    def test_product_price_must_be_positive(self) -> Any:
        """Проверяет сценарий `test_product_price_must_be_positive`."""
        self.auth(self.admin)
        response = self.client.post(
            '/api/v1/products/',
            {
                'name': 'Bad Price',
                'description': 'X',
                'price': '0.00',
                'stock_quantity': 5,
                'sku': 'SKU-BAD-0',
                'status': 'active',
                'is_active': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('price', response.data)

    def test_product_old_price_cannot_be_less_than_price(self) -> Any:
        """Проверяет сценарий `test_product_old_price_cannot_be_less_than_price`."""
        self.auth(self.admin)
        response = self.client.post(
            '/api/v1/products/',
            {
                'name': 'Bad Old Price',
                'description': 'X',
                'price': '1000.00',
                'old_price': '900.00',
                'stock_quantity': 5,
                'sku': 'SKU-BAD-OLD',
                'status': 'active',
                'is_active': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('old_price', response.data)

    def test_discount_category_validation_rejects_forbidden_category(self) -> Any:
        """Проверяет, что скидка недоступна для категорий вне разрешенного списка."""
        self.auth(self.admin)
        response = self.client.post(
            '/api/v1/products/',
            {
                'name': 'Forbidden Discount',
                'description': 'X',
                'price': '700.00',
                'old_price': '1000.00',
                'stock_quantity': 5,
                'sku': 'SKU-DISCOUNT-FORBIDDEN',
                'status': 'active',
                'is_active': True,
                'categories_ids': [self.discount_forbidden_category.id],
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('old_price', response.data)

    def test_discount_category_validation_allows_supported_category(self) -> Any:
        """Проверяет, что скидка доступна для разрешенной категории."""
        self.auth(self.admin)
        response = self.client.post(
            '/api/v1/products/',
            {
                'name': 'Allowed Discount',
                'description': 'X',
                'price': '700.00',
                'old_price': '1000.00',
                'stock_quantity': 5,
                'sku': 'SKU-DISCOUNT-ALLOWED',
                'status': 'active',
                'is_active': True,
                'categories_ids': [self.discount_allowed_category.id],
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)

    def test_product_get_discounted_price_works_correctly(self) -> Any:
        """Проверяет сценарий `test_product_get_discounted_price_works_correctly`."""
        product = Product.objects.create(
            name='Discounted',
            description='X',
            price=Decimal('1000.00'),
            stock_quantity=5,
            sku='SKU-DISC',
            status='active',
            is_active=True,
        )
        self.assertEqual(product.get_discounted_price(), Decimal('1000.00'))

    def test_cart_cannot_add_non_positive_quantity(self) -> Any:
        """Проверяет сценарий `test_cart_cannot_add_non_positive_quantity`."""
        self.auth(self.buyer)
        response = self.client.post('/api/v1/cart-items/', {'product_id': self.product_ok.id, 'quantity': 0}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_cart_cannot_add_archived_or_draft_or_out_of_stock_product(self) -> Any:
        """Проверяет сценарий `test_cart_cannot_add_archived_or_draft_or_out_of_stock_product`."""
        self.auth(self.buyer)
        for product in [self.product_archived, self.product_draft, self.product_oos]:
            response = self.client.post('/api/v1/cart-items/', {'product_id': product.id, 'quantity': 1}, format='json')
            self.assertEqual(response.status_code, 400)

    def test_order_total_model_validation_forbidden_when_non_positive(self) -> Any:
        """Проверяет сценарий `test_order_total_model_validation_forbidden_when_non_positive`."""
        order = Order(user=self.buyer, status=self.order_status, shipping_address='A', total=Decimal('0.00'))
        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_order_creation_failure_does_not_decrease_stock(self) -> Any:
        """Проверяет сценарий `test_order_creation_failure_does_not_decrease_stock`."""
        self.auth(self.buyer)
        CartItem.objects.create(cart=self.buyer.cart, product=self.product_low, quantity=1)
        before = self.product_low.stock_quantity
        response = self.client.post(
            '/api/v1/orders/',
            {'shipping_address': 'Улица Пушкина, д 10, Москва, 123456', 'notes': ''},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.product_low.refresh_from_db()
        self.assertEqual(self.product_low.stock_quantity, before)

    def test_admin_can_change_order_status(self) -> Any:
        """Проверяет сценарий `test_admin_can_change_order_status`."""
        order = Order.objects.create(user=self.buyer, status=self.order_status, shipping_address='A', total=1000)
        self.auth(self.admin)
        response = self.client.patch(f'/api/v1/orders/{order.id}/', {'status': self.completed_status.id}, format='json')
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status_id, self.completed_status.id)

    def test_review_cannot_be_left_for_new_order_status(self) -> Any:
        """Проверяет сценарий `test_review_cannot_be_left_for_new_order_status`."""
        self.auth(self.buyer)
        order = Order.objects.create(user=self.buyer, status=self.order_status, shipping_address='A', total=1000)
        OrderItem.objects.create(
            order=order,
            product=self.product_ok,
            product_name=self.product_ok.name,
            product_sku=self.product_ok.sku,
            price=self.product_ok.price,
            quantity=1,
        )
        response = self.client.post('/api/v1/reviews/', {'product': self.product_ok.id, 'rating': 5, 'comment': 'x'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_review_cannot_be_left_twice(self) -> Any:
        """Проверяет сценарий `test_review_cannot_be_left_twice`."""
        self.auth(self.buyer)
        order = Order.objects.create(user=self.buyer, status=self.completed_status, shipping_address='A', total=1000)
        OrderItem.objects.create(
            order=order,
            product=self.product_ok,
            product_name=self.product_ok.name,
            product_sku=self.product_ok.sku,
            price=self.product_ok.price,
            quantity=1,
        )
        self.assertEqual(
            self.client.post('/api/v1/reviews/', {'product': self.product_ok.id, 'rating': 5, 'comment': '1'}, format='json').status_code,
            201,
        )
        response_second = self.client.post('/api/v1/reviews/', {'product': self.product_ok.id, 'rating': 4, 'comment': '2'}, format='json')
        self.assertEqual(response_second.status_code, 400)

    def test_product_filter_by_fabric(self) -> Any:
        """Проверяет сценарий `test_product_filter_by_fabric`."""
        self.auth(self.buyer)
        response = self.client.get('/api/v1/products/?fabrics=cotton')
        self.assertEqual(response.status_code, 200)
        items = self._items(response)
        ids = {item['id'] for item in items}
        self.assertIn(self.product_ok.id, ids)

    def test_analytics_endpoint_forbidden_for_buyer(self) -> Any:
        """Проверяет сценарий `test_analytics_endpoint_forbidden_for_buyer`."""
        self.auth(self.buyer)
        response = self.client.get('/api/v1/analytics/products/')
        self.assertEqual(response.status_code, 403)

    def test_analytics_endpoint_available_for_admin_and_metrics_correct(self) -> Any:
        """Проверяет сценарий `test_analytics_endpoint_available_for_admin_and_metrics_correct`."""
        ProductFavorite.objects.create(user=self.buyer, product=self.product_ok)
        ProductFavorite.objects.create(user=self.other_user, product=self.product_ok)

        Review.objects.create(user=self.buyer, product=self.product_ok, rating=5, comment='great', is_verified_purchase=True)
        Review.objects.create(user=self.other_user, product=self.product_ok, rating=3, comment='ok', is_verified_purchase=True)

        paid_order = Order.objects.create(user=self.buyer, status=self.paid_status, shipping_address='A', total=1200)
        OrderItem.objects.create(
            order=paid_order,
            product=self.product_ok,
            product_name=self.product_ok.name,
            product_sku=self.product_ok.sku,
            price=Decimal('600.00'),
            quantity=2,
        )
        cancelled_order = Order.objects.create(user=self.buyer, status=self.cancelled_status, shipping_address='A', total=999)
        OrderItem.objects.create(
            order=cancelled_order,
            product=self.product_ok,
            product_name=self.product_ok.name,
            product_sku=self.product_ok.sku,
            price=Decimal('999.00'),
            quantity=1,
        )

        self.auth(self.admin)
        response = self.client.get('/api/v1/analytics/products/')
        self.assertEqual(response.status_code, 200)

        payload = response.data
        self.assertEqual(payload['orders_summary']['total_orders'], 2)
        self.assertEqual(payload['orders_summary']['paid_orders'], 1)
        self.assertEqual(payload['orders_summary']['cancelled_orders'], 1)
        self.assertEqual(Decimal(str(payload['orders_summary']['total_revenue'])), Decimal('1200.00'))

        sold_top = payload['top_sold_products'][0]
        self.assertEqual(sold_top['id'], self.product_ok.id)
        self.assertEqual(sold_top['sold_quantity'], 2)
        self.assertEqual(Decimal(str(sold_top['revenue'])), Decimal('1200.00'))

        rated_top = payload['top_rated_products'][0]
        self.assertEqual(rated_top['reviews_count'], 2)

        fav_top = payload['most_favorited_products'][0]
        self.assertEqual(fav_top['favorites_count'], 2)

    def test_cart_cannot_add_out_of_stock_product(self) -> Any:
        """Проверяет сценарий `test_cart_cannot_add_out_of_stock_product`."""
        self.auth(self.buyer)
        response = self.client.post('/api/v1/cart-items/', {'product_id': self.product_oos.id, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.data)

    def test_cart_cannot_add_more_than_stock(self) -> Any:
        """Проверяет сценарий `test_cart_cannot_add_more_than_stock`."""
        self.auth(self.buyer)
        response = self.client.post('/api/v1/cart-items/', {'product_id': self.product_low.id, 'quantity': 3}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_cart_merge_same_item_on_create(self) -> Any:
        """Проверяет сценарий `test_cart_merge_same_item_on_create`."""
        self.auth(self.buyer)
        self.client.post('/api/v1/cart-items/', {'product_id': self.product_ok.id, 'quantity': 1}, format='json')
        response = self.client.post('/api/v1/cart-items/', {'product_id': self.product_ok.id, 'quantity': 2}, format='json')
        self.assertEqual(response.status_code, 200)
        item = CartItem.objects.get(cart__user=self.buyer, product=self.product_ok)
        self.assertEqual(item.quantity, 3)

    def test_order_address_validation(self) -> Any:
        """Проверяет сценарий `test_order_address_validation`."""
        self.auth(self.buyer)
        CartItem.objects.create(cart=self.buyer.cart, product=self.product_ok, quantity=1)
        response = self.client.post('/api/v1/orders/', {'shipping_address': 'bad address', 'notes': ''}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('shipping_address', response.data)

    def test_order_total_min_validation(self) -> Any:
        """Проверяет сценарий `test_order_total_min_validation`."""
        self.auth(self.buyer)
        CartItem.objects.create(cart=self.buyer.cart, product=self.product_low, quantity=1)
        response = self.client.post(
            '/api/v1/orders/',
            {'shipping_address': 'Улица Пушкина, д 10, Москва, 123456', 'notes': ''},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.data)

    def test_order_from_cart_success_and_stock_decrease(self) -> Any:
        """Проверяет сценарий `test_order_from_cart_success_and_stock_decrease`."""
        self.auth(self.buyer)
        CartItem.objects.create(cart=self.buyer.cart, product=self.product_ok, quantity=2)
        response = self.client.post(
            '/api/v1/orders/',
            {'shipping_address': 'Улица Пушкина, д 10, Москва, 123456', 'notes': 'call me'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)

        order = Order.objects.get(user=self.buyer)
        self.assertEqual(order.items.count(), 1)
        self.product_ok.refresh_from_db()
        self.assertEqual(self.product_ok.stock_quantity, 8)
        self.assertFalse(self.buyer.cart.items.exists())

    def test_order_access_only_own_for_buyer(self) -> Any:
        """Проверяет сценарий `test_order_access_only_own_for_buyer`."""
        buyer_order = Order.objects.create(user=self.buyer, status=self.order_status, shipping_address='A', total=1000)
        OrderItem.objects.create(
            order=buyer_order,
            product=self.product_ok,
            product_name=self.product_ok.name,
            product_sku=self.product_ok.sku,
            price=self.product_ok.price,
            quantity=1,
        )
        other_order = Order.objects.create(user=self.other_user, status=self.order_status, shipping_address='B', total=1000)
        OrderItem.objects.create(
            order=other_order,
            product=self.product_ok,
            product_name=self.product_ok.name,
            product_sku=self.product_ok.sku,
            price=self.product_ok.price,
            quantity=1,
        )

        self.auth(self.buyer)
        response = self.client.get('/api/v1/orders/')
        self.assertEqual(response.status_code, 200)
        items = self._items(response)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['id'], buyer_order.id)

    def test_order_access_all_for_admin(self) -> Any:
        """Проверяет сценарий `test_order_access_all_for_admin`."""
        Order.objects.create(user=self.buyer, status=self.order_status, shipping_address='A', total=1000)
        Order.objects.create(user=self.other_user, status=self.order_status, shipping_address='B', total=1000)

        self.auth(self.admin)
        response = self.client.get('/api/v1/orders/')
        self.assertEqual(response.status_code, 200)
        items = self._items(response)
        self.assertEqual(len(items), 2)

    def test_buyer_cannot_update_order(self) -> Any:
        """Проверяет сценарий `test_buyer_cannot_update_order`."""
        order = Order.objects.create(user=self.buyer, status=self.order_status, shipping_address='A', total=1000)
        self.auth(self.buyer)
        response = self.client.patch(f'/api/v1/orders/{order.id}/', {'notes': 'new'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_review_only_after_purchase(self) -> Any:
        """Проверяет сценарий `test_review_only_after_purchase`."""
        self.auth(self.buyer)
        response = self.client.post('/api/v1/reviews/', {'product': self.product_ok.id, 'rating': 5, 'comment': 'great'}, format='json')
        self.assertEqual(response.status_code, 400)

        order = Order.objects.create(user=self.buyer, status=self.completed_status, shipping_address='A', total=1000)
        OrderItem.objects.create(
            order=order,
            product=self.product_ok,
            product_name=self.product_ok.name,
            product_sku=self.product_ok.sku,
            price=self.product_ok.price,
            quantity=1,
        )

        response_ok = self.client.post('/api/v1/reviews/', {'product': self.product_ok.id, 'rating': 5, 'comment': 'great'}, format='json')
        self.assertEqual(response_ok.status_code, 201)
        review = Review.objects.get(user=self.buyer, product=self.product_ok)
        self.assertTrue(review.is_verified_purchase)

    def test_product_filter_by_price(self) -> Any:
        """Проверяет сценарий `test_product_filter_by_price`."""
        self.auth(self.buyer)
        response = self.client.get('/api/v1/products/?min_price=500&max_price=650')
        self.assertEqual(response.status_code, 200)
        items = self._items(response)
        ids = {item['id'] for item in items}
        self.assertIn(self.product_ok.id, ids)
        self.assertNotIn(self.product_low.id, ids)

    def test_product_filter_by_category(self) -> Any:
        """Проверяет сценарий `test_product_filter_by_category`."""
        self.auth(self.buyer)
        response = self.client.get(f'/api/v1/products/?category={self.category.id}')
        self.assertEqual(response.status_code, 200)
        items = self._items(response)
        ids = {item['id'] for item in items}
        self.assertIn(self.product_ok.id, ids)

    def test_product_filter_by_category_slug(self) -> Any:
        """Проверяет фильтрацию по slug-категории (women/men/children)."""
        self.product_ok.published_pages = ['women']
        self.product_ok.save(update_fields=['published_pages'])

        self.auth(self.buyer)
        response = self.client.get('/api/v1/products/?category=women')
        self.assertEqual(response.status_code, 200)
        items = self._items(response)
        ids = {item['id'] for item in items}
        self.assertIn(self.product_ok.id, ids)

    def test_product_filter_by_supplier(self) -> Any:
        """Проверяет сценарий `test_product_filter_by_supplier`."""
        self.auth(self.buyer)
        response = self.client.get(f'/api/v1/products/?supplier={self.supplier.id}')
        self.assertEqual(response.status_code, 200)
        items = self._items(response)
        ids = {item['id'] for item in items}
        self.assertIn(self.product_ok.id, ids)

    def test_product_filter_by_color(self) -> Any:
        """Проверяет сценарий `test_product_filter_by_color`."""
        self.auth(self.buyer)
        response = self.client.get('/api/v1/products/?colors=black')
        self.assertEqual(response.status_code, 200)
        items = self._items(response)
        ids = {item['id'] for item in items}
        self.assertIn(self.product_ok.id, ids)

    def test_product_filter_by_size(self) -> Any:
        """Проверяет сценарий `test_product_filter_by_size`."""
        self.auth(self.buyer)
        response = self.client.get('/api/v1/products/?sizes=42')
        self.assertEqual(response.status_code, 200)
        items = self._items(response)
        ids = {item['id'] for item in items}
        self.assertIn(self.product_ok.id, ids)

    def test_non_admin_cannot_create_product(self) -> Any:
        """Проверяет сценарий `test_non_admin_cannot_create_product`."""
        self.auth(self.buyer)
        response = self.client.post(
            '/api/v1/products/',
            {
                'name': 'Sneaker X',
                'description': 'X',
                'price': '900.00',
                'stock_quantity': 5,
                'sku': 'SKU-X',
                'status': 'active',
                'is_active': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_product(self) -> Any:
        """Проверяет сценарий `test_admin_can_create_product`."""
        self.auth(self.admin)
        response = self.client.post(
            '/api/v1/products/',
            {
                'name': 'Sneaker Admin',
                'description': 'X',
                'price': '900.00',
                'stock_quantity': 5,
                'sku': 'SKU-ADMIN',
                'status': 'active',
                'is_active': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)

    def test_product_has_favorites_count_annotation(self) -> Any:
        """Проверяет сценарий `test_product_has_favorites_count_annotation`."""
        ProductFavorite.objects.create(user=self.buyer, product=self.product_ok)
        ProductFavorite.objects.create(user=self.other_user, product=self.product_ok)

        self.auth(self.buyer)
        response = self.client.get('/api/v1/products/')
        self.assertEqual(response.status_code, 200)

        items = self._items(response)
        product_data = next(item for item in items if item['id'] == self.product_ok.id)
        self.assertEqual(product_data['favorites_count'], 2)

    def test_favorites_add_list_delete(self) -> Any:
        """Проверяет сценарий `test_favorites_add_list_delete`."""
        self.auth(self.buyer)

        create_response = self.client.post('/api/v1/favorites/', {'product_id': self.product_ok.id}, format='json')
        self.assertEqual(create_response.status_code, 201)
        favorite_id = create_response.data['id']

        list_response = self.client.get('/api/v1/favorites/')
        self.assertEqual(list_response.status_code, 200)
        items = self._items(list_response)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['product']['id'], self.product_ok.id)

        delete_response = self.client.delete(f'/api/v1/favorites/{favorite_id}/')
        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(ProductFavorite.objects.filter(user=self.buyer).count(), 0)
