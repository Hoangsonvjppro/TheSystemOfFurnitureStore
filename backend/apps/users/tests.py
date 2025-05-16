from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import User, UserShippingAddress
from apps.inventory.models import Branch

User = get_user_model()


class UserModelTest(TestCase):
    """Tests for custom User model"""

    def setUp(self):
        self.branch = Branch.objects.create(
            name='Test Branch',
            address='123 Test St',
            city='Test City',
            phone='1234567890'
        )

        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            full_name='Admin User',
            role='ADMIN',
            is_staff=True
        )

        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='manager123',
            full_name='Manager User',
            role='MANAGER',
            branch=self.branch
        )

        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='customer123',
            full_name='Customer User',
            role='CUSTOMER'
        )

    def test_user_creation(self):
        """Test users are created correctly"""
        self.assertEqual(self.admin_user.full_name, 'Admin User')
        self.assertEqual(self.admin_user.email, 'admin@example.com')
        self.assertEqual(self.admin_user.role, 'ADMIN')
        self.assertTrue(self.admin_user.is_staff)

        self.assertEqual(self.manager_user.role, 'MANAGER')
        self.assertEqual(self.manager_user.branch, self.branch)

        self.assertEqual(self.customer_user.role, 'CUSTOMER')
        self.assertIsNone(self.customer_user.branch)

    def test_role_methods(self):
        """Test user role methods"""
        self.assertTrue(self.admin_user.is_admin())
        self.assertFalse(self.admin_user.is_manager())
        self.assertFalse(self.admin_user.is_customer())

        self.assertTrue(self.manager_user.is_manager())
        self.assertFalse(self.manager_user.is_admin())

        self.assertTrue(self.customer_user.is_customer())
        self.assertFalse(self.customer_user.is_staff)
        self.assertFalse(self.customer_user.is_inventory_staff())


class UserShippingAddressTest(TestCase):
    """Tests for UserShippingAddress model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='customer123',
            full_name='Customer User',
            role='CUSTOMER'
        )

        self.address1 = UserShippingAddress.objects.create(
            user=self.user,
            recipient_name='Customer User',
            phone='1234567890',
            address='123 Home St',
            city='Home City',
            postal_code='12345'
        )

    def test_address_creation(self):
        """Test shipping address is created correctly"""
        self.assertEqual(self.address1.recipient_name, 'Customer User')
        self.assertEqual(self.address1.city, 'Home City')
        self.assertTrue(self.address1.is_default)  # First address should be default

    def test_multiple_addresses(self):
        """Test multiple shipping addresses for a user"""
        address2 = UserShippingAddress.objects.create(
            user=self.user,
            recipient_name='Work Address',
            phone='0987654321',
            address='456 Work Ave',
            city='Work City',
            is_default=True
        )

        # Reload address1 from database
        self.address1.refresh_from_db()

        # address1 should no longer be default
        self.assertFalse(self.address1.is_default)
        self.assertTrue(address2.is_default)


class UserAPITest(APITestCase):
    """Tests for User API"""

    def setUp(self):
        self.branch = Branch.objects.create(
            name='Test Branch',
            address='123 Test St',
            city='Test City',
            phone='1234567890'
        )

        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            full_name='Admin User',
            role='ADMIN',
            is_staff=True
        )

        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='manager123',
            full_name='Manager User',
            role='MANAGER',
            branch=self.branch
        )

        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='customer123',
            full_name='Customer User',
            role='CUSTOMER'
        )

        self.client = APIClient()
        self.users_url = reverse('users:user-list')
        self.customer_detail_url = reverse('users:user-detail', kwargs={'pk': self.customer_user.id})
        self.register_url = reverse('users:register')
        self.me_url = reverse('users:me')

    def test_list_users_as_admin(self):
        """Test listing users as admin"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.users_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # All users

    def test_list_users_as_customer(self):
        """Test listing users as customer (should fail)"""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.users_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user_as_admin(self):
        """Test creating user as admin"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'username': 'newstaff',
            'email': 'staff@example.com',
            'password': 'staff123',
            'full_name': 'Staff User',
            'role': 'SALES_STAFF',
            'branch': self.branch.id
        }
        response = self.client.post(self.users_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'staff@example.com')
        self.assertEqual(response.data['role'], 'SALES_STAFF')

    def test_update_user_as_admin(self):
        """Test updating user as admin"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'full_name': 'Updated Customer Name',
            'phone': '9876543210'
        }
        response = self.client.patch(self.customer_detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'Updated Customer Name')

    def test_update_user_as_self(self):
        """Test updating own profile"""
        self.client.force_authenticate(user=self.customer_user)
        data = {
            'full_name': 'My New Name',
            'phone': '5555555555'
        }
        response = self.client.patch(self.me_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'My New Name')

    def test_update_other_user_as_customer(self):
        """Test updating another user as customer (should fail)"""
        self.client.force_authenticate(user=self.customer_user)
        manager_url = reverse('users:user-detail', kwargs={'pk': self.manager_user.id})
        data = {
            'full_name': 'Hacked Name'
        }
        response = self.client.patch(manager_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_new_user(self):
        """Test registering a new user"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newuser123',
            'full_name': 'New User'
        }
        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'newuser@example.com')
        self.assertEqual(response.data['role'], 'CUSTOMER')  # Default role is CUSTOMER


class UserShippingAddressAPITest(APITestCase):
    """Tests for UserShippingAddress API"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='customer123',
            full_name='Customer User',
            role='CUSTOMER'
        )

        self.address = UserShippingAddress.objects.create(
            user=self.user,
            recipient_name='Customer User',
            phone='1234567890',
            address='123 Home St',
            city='Home City',
            postal_code='12345'
        )

        self.client = APIClient()
        self.addresses_url = reverse('users:shipping-address-list')
        self.address_detail_url = reverse('users:shipping-address-detail', kwargs={'pk': self.address.id})

    def test_list_addresses(self):
        """Test listing user's shipping addresses"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.addresses_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['recipient_name'], 'Customer User')

    def test_create_address(self):
        """Test creating a new shipping address"""
        self.client.force_authenticate(user=self.user)
        data = {
            'recipient_name': 'Work Address',
            'phone': '9876543210',
            'address': '456 Work Ave',
            'city': 'Work City',
            'postal_code': '54321',
            'is_default': True
        }
        response = self.client.post(self.addresses_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['recipient_name'], 'Work Address')
        self.assertTrue(response.data['is_default'])

        # Original address should no longer be default
        response = self.client.get(self.address_detail_url)
        self.assertFalse(response.data['is_default'])

    def test_update_address(self):
        """Test updating a shipping address"""
        self.client.force_authenticate(user=self.user)
        data = {
            'recipient_name': 'Updated Name',
            'phone': '5555555555'
        }
        response = self.client.patch(self.address_detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['recipient_name'], 'Updated Name')
        self.assertEqual(response.data['phone'], '5555555555')

    def test_delete_address(self):
        """Test deleting a shipping address"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.address_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserShippingAddress.objects.count(), 0)