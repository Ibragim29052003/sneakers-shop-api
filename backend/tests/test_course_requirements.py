from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from carts.models import Cart, CartItem
from orders.models import Order, OrderItem, OrderStatus
from products.models import Product, ProductFavorite
from reviews.models import Review
from users.models import Role, UserRole


class CourseRequirementsAPITests(TestCase):
    def setUp(self):
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
            is_active=True,
        )

        Cart.objects.get_or_create(user=self.buyer)
        Cart.objects.get_or_create(user=self.other_user)

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def _items(self, response):
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data

    def test_cart_cannot_add_out_of_stock_product(self):
        self.auth(self.buyer)
        response = self.client.post('/api/v1/cart-items/', {'product_id': self.product_oos.id, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.data)

    def test_cart_cannot_add_more_than_stock(self):
        self.auth(self.buyer)
        response = self.client.post('/api/v1/cart-items/', {'product_id': self.product_low.id, 'quantity': 3}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_cart_merge_same_item_on_create(self):
        self.auth(self.buyer)
        self.client.post('/api/v1/cart-items/', {'product_id': self.product_ok.id, 'quantity': 1}, format='json')
        response = self.client.post('/api/v1/cart-items/', {'product_id': self.product_ok.id, 'quantity': 2}, format='json')
        self.assertEqual(response.status_code, 200)
        item = CartItem.objects.get(cart__user=self.buyer, product=self.product_ok)
        self.assertEqual(item.quantity, 3)

    def test_order_address_validation(self):
        self.auth(self.buyer)
        CartItem.objects.create(cart=self.buyer.cart, product=self.product_ok, quantity=1)
        response = self.client.post('/api/v1/orders/', {'shipping_address': 'bad address', 'notes': ''}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('shipping_address', response.data)

    def test_order_total_min_validation(self):
        self.auth(self.buyer)
        CartItem.objects.create(cart=self.buyer.cart, product=self.product_low, quantity=1)
        response = self.client.post(
            '/api/v1/orders/',
            {'shipping_address': 'Улица Пушкина, д 10, Москва, 123456', 'notes': ''},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.data)

    def test_order_from_cart_success_and_stock_decrease(self):
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

    def test_order_access_only_own_for_buyer(self):
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

    def test_order_access_all_for_admin(self):
        Order.objects.create(user=self.buyer, status=self.order_status, shipping_address='A', total=1000)
        Order.objects.create(user=self.other_user, status=self.order_status, shipping_address='B', total=1000)

        self.auth(self.admin)
        response = self.client.get('/api/v1/orders/')
        self.assertEqual(response.status_code, 200)
        items = self._items(response)
        self.assertEqual(len(items), 2)

    def test_buyer_cannot_update_order(self):
        order = Order.objects.create(user=self.buyer, status=self.order_status, shipping_address='A', total=1000)
        self.auth(self.buyer)
        response = self.client.patch(f'/api/v1/orders/{order.id}/', {'notes': 'new'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_review_only_after_purchase(self):
        self.auth(self.buyer)
        response = self.client.post('/api/v1/reviews/', {'product': self.product_ok.id, 'rating': 5, 'comment': 'great'}, format='json')
        self.assertEqual(response.status_code, 400)

        order = Order.objects.create(user=self.buyer, status=self.order_status, shipping_address='A', total=1000)
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

    def test_product_filter_by_price(self):
        self.auth(self.buyer)
        response = self.client.get('/api/v1/products/?min_price=500&max_price=650')
        self.assertEqual(response.status_code, 200)
        items = self._items(response)
        ids = {item['id'] for item in items}
        self.assertIn(self.product_ok.id, ids)
        self.assertNotIn(self.product_low.id, ids)

    def test_product_has_favorites_count_annotation(self):
        ProductFavorite.objects.create(user=self.buyer, product=self.product_ok)
        ProductFavorite.objects.create(user=self.other_user, product=self.product_ok)

        self.auth(self.buyer)
        response = self.client.get('/api/v1/products/')
        self.assertEqual(response.status_code, 200)

        items = self._items(response)
        product_data = next(item for item in items if item['id'] == self.product_ok.id)
        self.assertEqual(product_data['favorites_count'], 2)

    def test_favorites_add_list_delete(self):
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
