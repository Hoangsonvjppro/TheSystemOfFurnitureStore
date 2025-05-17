from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Branch, Stock, StockMovement
from apps.products.models import Product, ProductVariant

User = get_user_model()


class BranchModelTest(TestCase):
    """Test for Branch model"""

    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager1',
            email='manager@example.com',
            password='password123',
            full_name='Test Manager',
            role='MANAGER'
        )

        self.branch = Branch.objects.create(
            name='Test Branch',
            address='123 Test Street',
            city='Test City',
            phone='1234567890',
            email='branch@example.com',
            manager=self.manager
        )

    def test_branch_creation(self):
        """Test that branch is created correctly"""
        self.assertEqual(self.branch.name, 'Test Branch')
        self.assertEqual(self.branch.city, 'Test City')
        self.assertEqual(self.branch.manager, self.manager)
        self.assertTrue(self.branch.is_active)


class StockModelTest(TestCase):
    """Test for Stock model"""

    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager1',
            email='manager@example.com',
            password='password123',
            full_name='Test Manager',
            role='MANAGER'
        )

        self.branch = Branch.objects.create(
            name='Test Branch',
            address='123 Test Street',
            city='Test City',
            phone='1234567890',
            manager=self.manager
        )

        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=100.00,
            sku='TP001'
        )

        self.stock = Stock.objects.create(
            branch=self.branch,
            product=self.product,
            quantity=10,
            reorder_level=5
        )

    def test_stock_creation(self):
        """Test that stock is created correctly"""
        self.assertEqual(self.stock.branch, self.branch)
        self.assertEqual(self.stock.product, self.product)
        self.assertEqual(self.stock.quantity, 10)
        self.assertEqual(self.stock.reorder_level, 5)

    def test_is_low_stock_property(self):
        """Test the is_low_stock property"""
        self.assertFalse(self.stock.is_low_stock)

        # Reduce stock below reorder level
        self.stock.quantity = 3
        self.stock.save()
        self.assertTrue(self.stock.is_low_stock)

        # At reorder level should still be considered low
        self.stock.quantity = 5
        self.stock.save()
        self.assertTrue(self.stock.is_low_stock)


class StockMovementModelTest(TestCase):
    """Test for StockMovement model"""

    def setUp(self):
        self.staff = User.objects.create_user(
            username='staff1',
            email='staff@example.com',
            password='password123',
            full_name='Test Staff',
            role='INVENTORY_STAFF'
        )

        self.branch = Branch.objects.create(
            name='Test Branch',
            address='123 Test Street',
            city='Test City',
            phone='1234567890'
        )

        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=100.00,
            sku='TP001'
        )

        self.stock = Stock.objects.create(
            branch=self.branch,
            product=self.product,
            quantity=10,
            reorder_level=5
        )

    def test_addition_movement(self):
        """Test stock addition movement"""
        movement = StockMovement.objects.create(
            stock=self.stock,
            quantity=5,
            movement_type='ADDITION',
            reference='PO123',
            notes='Initial stock',
            performed_by=self.staff
        )

        self.assertEqual(movement.quantity, 5)
        self.assertEqual(movement.movement_type, 'ADDITION')
        self.assertEqual(movement.stock, self.stock)
        self.assertEqual(movement.performed_by, self.staff)


class BranchAPITest(APITestCase):
    """Test the Branch API"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin1',
            email='admin@example.com',
            password='password123',
            full_name='Test Admin',
            role='ADMIN',
            is_staff=True
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.branch_data = {
            'name': 'API Test Branch',
            'address': '123 API Street',
            'city': 'API City',
            'phone': '9876543210',
            'email': 'api@example.com'
        }

        self.branch_url = reverse('inventory:branch-list')

    def test_create_branch(self):
        """Test creating a branch via API"""
        response = self.client.post(self.branch_url, self.branch_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Branch.objects.count(), 1)
        self.assertEqual(Branch.objects.get().name, 'API Test Branch')

    def test_list_branches(self):
        """Test listing branches via API"""
        Branch.objects.create(**self.branch_data)
        response = self.client.get(self.branch_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.branch_data['name'])


class StockAPITest(APITestCase):
    """Test the Stock API"""

    def setUp(self):
        self.inventory_staff = User.objects.create_user(
            username='inventory1',
            email='inventory@example.com',
            password='password123',
            full_name='Test Inventory',
            role='INVENTORY_STAFF'
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.inventory_staff)

        self.branch = Branch.objects.create(
            name='API Test Branch',
            address='123 API Street',
            city='API City',
            phone='9876543210'
        )

        self.product = Product.objects.create(
            name='API Test Product',
            slug='api-test-product',
            description='API Test description',
            price=100.00,
            sku='ATP001'
        )

        self.stock = Stock.objects.create(
            branch=self.branch,
            product=self.product,
            quantity=20,
            reorder_level=5
        )

        self.stock_url = reverse('inventory:stock-list')

    def test_list_stocks(self):
        """Test listing stocks via API"""
        response = self.client.get(self.stock_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_adjust_stock(self):
        """Test adjusting stock quantity via API"""
        adjust_url = reverse('inventory:stock-adjust', kwargs={'pk': self.stock.pk})
        response = self.client.post(adjust_url, {'quantity': 25, 'notes': 'API Test adjustment'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh stock from database
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 25)

        # Check movement record was created
        movement = StockMovement.objects.latest('created_at')
        self.assertEqual(movement.movement_type, 'ADDITION')
        self.assertEqual(movement.quantity, 5)  # 25 - 20 = 5
        self.assertEqual(movement.notes, 'API Test adjustment')

    def test_inventory_report(self):
        """Test inventory report generation"""
        # Create some test data
        self.stock.quantity = 0  # Out of stock
        self.stock.save()

        another_product = Product.objects.create(
            name='Another Product',
            slug='another-product',
            description='Another test description',
            price=150.00,
            sku='ATP002'
        )

        low_stock = Stock.objects.create(
            branch=self.branch,
            product=another_product,
            quantity=3,
            reorder_level=5
        )

        # Create some movements
        StockMovement.objects.create(
            stock=self.stock,
            quantity=5,
            movement_type='ADDITION',
            performed_by=self.inventory_staff
        )

        StockMovement.objects.create(
            stock=low_stock,
            quantity=2,
            movement_type='REMOVAL',
            performed_by=self.inventory_staff
        )

        # Test report
        report_url = reverse('inventory:stock-inventory-report')
        response = self.client.get(report_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # Check statistics
        self.assertEqual(data['statistics']['total_products'], 2)
        self.assertEqual(data['statistics']['out_of_stock'], 1)
        self.assertEqual(data['statistics']['low_stock'], 1)

        # Check low stock items
        self.assertEqual(len(data['low_stock_items']), 1)
        self.assertEqual(data['low_stock_items'][0]['product'], another_product.id)

        # Check out of stock items
        self.assertEqual(len(data['out_of_stock_items']), 1)
        self.assertEqual(data['out_of_stock_items'][0]['product'], self.product.id)

        # Check movement statistics
        movement_stats = {m['movement_type']: m for m in data['movement_statistics']}
        self.assertEqual(movement_stats['ADDITION']['count'], 1)
        self.assertEqual(movement_stats['REMOVAL']['count'], 1)
        self.assertEqual(movement_stats['ADDITION']['total_quantity'], 5)
        self.assertEqual(movement_stats['REMOVAL']['total_quantity'], 2)