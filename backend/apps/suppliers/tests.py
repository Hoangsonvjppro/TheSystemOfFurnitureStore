from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import json

from .models import Supplier, SupplierContact, PurchaseOrder

User = get_user_model()


class SupplierModelTest(TestCase):
    """Test the Supplier model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            code='TEST001',
            address='123 Test Street',
            city='Test City',
            postal_code='12345',
            phone='123-456-7890',
            email='supplier@test.com',
            assigned_to=self.user
        )

    def test_supplier_creation(self):
        """Test creating a supplier"""
        self.assertEqual(self.supplier.name, 'Test Supplier')
        self.assertEqual(self.supplier.code, 'TEST001')
        self.assertEqual(self.supplier.email, 'supplier@test.com')
        self.assertEqual(self.supplier.assigned_to, self.user)
        self.assertTrue(self.supplier.is_active)

    def test_supplier_str(self):
        """Test the supplier string representation"""
        self.assertEqual(str(self.supplier), 'Test Supplier (TEST001)')


class SupplierContactModelTest(TestCase):
    """Test the SupplierContact model"""

    def setUp(self):
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            code='TEST001',
            address='123 Test Street',
            city='Test City',
            postal_code='12345',
            phone='123-456-7890',
            email='supplier@test.com'
        )
        self.contact = SupplierContact.objects.create(
            supplier=self.supplier,
            name='John Doe',
            title='Sales Manager',
            phone='987-654-3210',
            email='john@testsupplier.com',
            is_primary=True
        )

    def test_contact_creation(self):
        """Test creating a supplier contact"""
        self.assertEqual(self.contact.name, 'John Doe')
        self.assertEqual(self.contact.title, 'Sales Manager')
        self.assertEqual(self.contact.email, 'john@testsupplier.com')
        self.assertTrue(self.contact.is_primary)

    def test_contact_str(self):
        """Test the contact string representation"""
        self.assertEqual(str(self.contact), 'John Doe (Test Supplier)')

    def test_single_primary_contact(self):
        """Test that only one contact can be primary"""
        # Create a new primary contact
        contact2 = SupplierContact.objects.create(
            supplier=self.supplier,
            name='Jane Smith',
            title='Purchase Manager',
            phone='555-123-4567',
            email='jane@testsupplier.com',
            is_primary=True
        )

        # Refresh the first contact from db
        self.contact.refresh_from_db()

        # The first contact should no longer be primary
        self.assertFalse(self.contact.is_primary)
        self.assertTrue(contact2.is_primary)


class SupplierAPITest(APITestCase):
    """Test the supplier API"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            code='TEST001',
            address='123 Test Street',
            city='Test City',
            postal_code='12345',
            phone='123-456-7890',
            email='supplier@test.com'
        )

    def test_list_suppliers(self):
        """Test retrieving a list of suppliers"""
        url = reverse('suppliers:suppliers-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_supplier(self):
        """Test creating a new supplier"""
        url = reverse('suppliers:suppliers-list')
        data = {
            'name': 'New Supplier',
            'code': 'NEW001',
            'address': '456 New Street',
            'city': 'New City',
            'postal_code': '54321',
            'phone': '555-123-4567',
            'email': 'new@supplier.com',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Supplier.objects.count(), 2)

    def test_retrieve_supplier(self):
        """Test retrieving a supplier detail"""
        url = reverse('suppliers:suppliers-detail', args=[self.supplier.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Supplier')

    def test_update_supplier(self):
        """Test updating a supplier"""
        url = reverse('suppliers:suppliers-detail', args=[self.supplier.id])
        data = {
            'name': 'Updated Supplier',
            'code': 'TEST001',
            'address': '123 Test Street',
            'city': 'Test City',
            'postal_code': '12345',
            'phone': '123-456-7890',
            'email': 'updated@supplier.com',
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.name, 'Updated Supplier')
        self.assertEqual(self.supplier.email, 'updated@supplier.com')