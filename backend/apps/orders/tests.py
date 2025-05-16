from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import Cart, CartItem, Order, OrderItem, OrderTracking
from apps.products.models import Product, ProductVariant, Category
from apps.inventory.models import Branch

User = get_user_model()


class CartModelTest(TestCase):
    """Tests for Cart model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            full_name='Test User',
            role='CUSTOMER'
        )

        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('100.00'),
            sku='TP001',
            category=self.category
        )

        self.cart = Cart.objects.create(user=self.user)

    def test_cart_creation(self):
        """Test cart is created correctly"""
        self.assertEqual(self.cart.user, self.user)
        self.assertEqual(self.cart.total_items, 0)
        self.assertEqual(self.cart.subtotal, 0)

    def test_add_item_to_cart(self):
        """Test adding item to cart"""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

        self.assertEqual(self.cart.total_items, 2)
        self.assertEqual(self.cart.subtotal, Decimal('200.00'))
        self.assertEqual(cart_item.line_total, Decimal('200.00'))


class OrderModelTest(TestCase):
    """Tests for Order model"""

    def setUp(self):
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password123',
            full_name='Customer User',
            role='CUSTOMER'
        )

        self.staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='password123',
            full_name='Staff User',
            role='SALES_STAFF'
        )

        self.branch = Branch.objects.create(
            name='Test Branch',
            address='123 Test St',
            city='Test City',
            phone='1234567890'
        )

        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('100.00'),
            sku='TP001',
            category=self.category
        )

        self.order = Order.objects.create(
            user=self.customer,
            branch=self.branch,
            shipping_name='Test Customer',
            shipping_phone='9876543210',
            shipping_address_line='456 Customer St',
            shipping_city='Customer City',
            subtotal=Decimal('100.00'),
            total=Decimal('100.00')
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name=self.product.name,
            sku=self.product.sku,
            quantity=1,
            unit_price=Decimal('100.00'),
            line_total=Decimal('100.00')
        )

    def test_order_creation(self):
        """Test order is created correctly"""
        self.assertIsNotNone(self.order.order_number)
        self.assertEqual(self.order.status, 'PENDING')
        self.assertEqual(self.order.payment_status, 'PENDING')
        self.assertEqual(self.order.total, Decimal('100.00'))

    def test_order_status_update(self):
        """Test order status updates correctly"""
        # Change to confirmed
        self.order.status = 'CONFIRMED'
        self.order.save()
        self.assertEqual(self.order.status, 'CONFIRMED')
        self.assertIsNotNone(self.order.confirmed_at)

        # Change to shipped
        self.order.status = 'SHIPPED'
        self.order.save()
        self.assertEqual(self.order.status, 'SHIPPED')
        self.assertIsNotNone(self.order.shipped_at)

        # Change to delivered
        self.order.status = 'DELIVERED'
        self.order.save()
        self.assertEqual(self.order.status, 'DELIVERED')
        self.assertIsNotNone(self.order.delivered_at)

        # Change to cancelled
        self.order.status = 'CANCELLED'
        self.order.save()
        self.assertEqual(self.order.status, 'CANCELLED')
        self.assertIsNotNone(self.order.cancelled_at)


class OrderTrackingModelTest(TestCase):
    """Tests for OrderTracking model"""

    def setUp(self):
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password123',
            full_name='Customer User',
            role='CUSTOMER'
        )

        self.staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='password123',
            full_name='Staff User',
            role='SALES_STAFF'
        )

        self.branch = Branch.objects.create(
            name='Test Branch',
            address='123 Test St',
            city='Test City',
            phone='1234567890'
        )

        self.order = Order.objects.create(
            user=self.customer,
            branch=self.branch,
            shipping_name='Test Customer',
            shipping_phone='9876543210',
            shipping_address_line='456 Customer St',
            shipping_city='Customer City',
            subtotal=Decimal('100.00'),
            total=Decimal('100.00')
        )

    def test_tracking_creation(self):
        """Test order tracking is created correctly"""
        tracking = OrderTracking.objects.create(
            order=self.order,
            status='PENDING',
            notes='Order placed',
            performed_by=self.customer
        )

        self.assertEqual(tracking.order, self.order)
        self.assertEqual(tracking.status, 'PENDING')
        self.assertEqual(tracking.performed_by, self.customer)

        # Add another tracking entry
        tracking2 = OrderTracking.objects.create(
            order=self.order,
            status='CONFIRMED',
            notes='Order confirmed',
            performed_by=self.staff
        )

        self.assertEqual(tracking2.status, 'CONFIRMED')
        self.assertEqual(tracking2.performed_by, self.staff)

        # Check order tracking history
        self.assertEqual(self.order.tracking_history.count(), 2)


class CartAPITest(APITestCase):
    """Tests for Cart API"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            full_name='Test User',
            role='CUSTOMER'
        )

        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('100.00'),
            sku='TP001',
            category=self.category,
            is_active=True
        )

        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='TP001-V1',
            is_active=True
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.cart_url = reverse('orders:cart-list')
        self.add_item_url = reverse('orders:cart-add-item')

    def test_get_cart(self):
        """Test retrieving user's cart"""
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(response.data['total_items'], 0)

    def test_add_item_to_cart(self):
        """Test adding item to cart via API"""
        data = {
            'product': self.product.id,
            'quantity': 2
        }
        response = self.client.post(self.add_item_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 2)
        self.assertEqual(len(response.data['items']), 1)

        # Add variant to cart
        data = {
            'product': self.product.id,
            'variant': self.variant.id,
            'quantity': 1
        }
        response = self.client.post(self.add_item_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 3)
        self.assertEqual(len(response.data['items']), 2)


class OrderAPITest(APITestCase):
    """Tests for Order API"""

    def setUp(self):
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password123',
            full_name='Customer User',
            role='CUSTOMER'
        )

        self.staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='password123',
            full_name='Staff User',
            role='SALES_STAFF',
            is_staff=True
        )

        self.branch = Branch.objects.create(
            name='Test Branch',
            address='123 Test St',
            city='Test City',
            phone='1234567890'
        )

        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('100.00'),
            sku='TP001',
            category=self.category,
            is_active=True
        )

        # Create cart and add item for testing order creation
        self.cart = Cart.objects.create(user=self.customer)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

        # Create an order for testing
        self.order = Order.objects.create(
            user=self.customer,
            branch=self.branch,
            shipping_name='Test Customer',
            shipping_phone='9876543210',
            shipping_address_line='456 Customer St',
            shipping_city='Customer City',
            subtotal=Decimal('200.00'),
            total=Decimal('200.00')
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name=self.product.name,
            sku=self.product.sku,
            quantity=2,
            unit_price=Decimal('100.00'),
            line_total=Decimal('200.00')
        )

        self.client = APIClient()
        self.orders_url = reverse('orders:order-list')
        self.order_detail_url = reverse('orders:order-detail', kwargs={'pk': self.order.id})

    def test_list_customer_orders(self):
        """Test customer can see their own orders"""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(self.orders_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_staff_can_update_order(self):
        """Test staff can update order status"""
        self.client.force_authenticate(user=self.staff)

        # Update to confirmed
        url = reverse('orders:order-update-status', kwargs={'pk': self.order.id})
        data = {'status': 'CONFIRMED', 'notes': 'Order confirmed by staff'}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'CONFIRMED')

        # Check tracking was created
        self.assertEqual(OrderTracking.objects.filter(order=self.order).count(), 1)

    def test_customer_can_cancel_order(self):
        """Test customer can cancel their pending order"""
        self.client.force_authenticate(user=self.customer)

        # Cancel order
        url = reverse('orders:order-cancel', kwargs={'pk': self.order.id})
        response = self.client.post(url, {'notes': 'Changed my mind'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'CANCELLED')
        self.assertIsNotNone(response.data['cancelled_at'])
