from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import (
    Category, Product, ProductAttribute, ProductAttributeValue,
    ProductVariant, ProductImage, ProductReview, Wishlist, WishlistItem
)

User = get_user_model()


class CategoryModelTest(TestCase):
    """Tests for Category model"""

    def setUp(self):
        self.parent_category = Category.objects.create(
            name='Furniture',
            slug='furniture',
            description='All furniture items'
        )

        self.child_category = Category.objects.create(
            name='Chairs',
            slug='chairs',
            description='All types of chairs',
            parent=self.parent_category
        )

    def test_category_creation(self):
        """Test category is created correctly"""
        self.assertEqual(self.parent_category.name, 'Furniture')
        self.assertEqual(self.parent_category.slug, 'furniture')
        self.assertIsNone(self.parent_category.parent)

        self.assertEqual(self.child_category.name, 'Chairs')
        self.assertEqual(self.child_category.parent, self.parent_category)

    def test_category_hierarchy(self):
        """Test MPTT hierarchy functionality"""
        self.assertTrue(self.child_category in self.parent_category.get_children())
        self.assertEqual(self.child_category.get_ancestors().count(), 1)
        self.assertTrue(self.parent_category in self.child_category.get_ancestors())


class ProductModelTest(TestCase):
    """Tests for Product model"""

    def setUp(self):
        self.category = Category.objects.create(
            name='Chairs',
            slug='chairs',
            description='All types of chairs'
        )

        self.attribute = ProductAttribute.objects.create(
            name='color',
            display_name='Color'
        )

        self.product = Product.objects.create(
            name='Ergonomic Chair',
            slug='ergonomic-chair',
            description='A comfortable ergonomic chair',
            price=Decimal('199.99'),
            discount_price=Decimal('179.99'),
            category=self.category,
            sku='EC001',
            is_active=True,
            is_featured=True
        )

        self.attribute_value = ProductAttributeValue.objects.create(
            product=self.product,
            attribute=self.attribute,
            value='Black'
        )

        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='EC001-RED',
            price=Decimal('209.99')
        )

        self.image = ProductImage.objects.create(
            product=self.product,
            image='test.jpg',
            is_primary=True,
            alt_text='Test Image'
        )

    def test_product_creation(self):
        """Test product is created correctly"""
        self.assertEqual(self.product.name, 'Ergonomic Chair')
        self.assertEqual(self.product.price, Decimal('199.99'))
        self.assertEqual(self.product.category, self.category)
        self.assertTrue(self.product.is_active)
        self.assertTrue(self.product.is_featured)

    def test_product_properties(self):
        """Test product property methods"""
        self.assertAlmostEqual(self.product.discount_percentage, Decimal('10.0'), places=1)
        self.assertEqual(self.product.final_price, Decimal('179.99'))
        self.assertEqual(self.product.main_image, self.image)

    def test_product_variant(self):
        """Test product variant relationship"""
        self.assertEqual(self.variant.product, self.product)
        self.assertEqual(self.variant.final_price, Decimal('209.99'))

    def test_product_attribute(self):
        """Test product attribute relationship"""
        self.assertEqual(self.attribute_value.product, self.product)
        self.assertEqual(self.attribute_value.attribute, self.attribute)
        self.assertEqual(self.attribute_value.value, 'Black')


class ProductReviewTest(TestCase):
    """Tests for ProductReview model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            full_name='Test User'
        )

        self.category = Category.objects.create(
            name='Chairs',
            slug='chairs'
        )

        self.product = Product.objects.create(
            name='Ergonomic Chair',
            slug='ergonomic-chair',
            description='A comfortable ergonomic chair',
            price=Decimal('199.99'),
            category=self.category,
            sku='EC001'
        )

        self.review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            comment='Great chair, very comfortable',
            is_approved=True
        )

    def test_review_creation(self):
        """Test review is created correctly"""
        self.assertEqual(self.review.product, self.product)
        self.assertEqual(self.review.user, self.user)
        self.assertEqual(self.review.rating, 4)
        self.assertTrue(self.review.is_approved)


class WishlistTest(TestCase):
    """Tests for Wishlist model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            full_name='Test User'
        )

        self.category = Category.objects.create(
            name='Chairs',
            slug='chairs'
        )

        self.product = Product.objects.create(
            name='Ergonomic Chair',
            slug='ergonomic-chair',
            description='A comfortable ergonomic chair',
            price=Decimal('199.99'),
            category=self.category,
            sku='EC001'
        )

        self.wishlist = Wishlist.objects.create(user=self.user)
        self.wishlist_item = WishlistItem.objects.create(
            wishlist=self.wishlist,
            product=self.product
        )

    def test_wishlist_creation(self):
        """Test wishlist is created correctly"""
        self.assertEqual(self.wishlist.user, self.user)
        self.assertEqual(self.wishlist.items.count(), 1)
        self.assertEqual(self.wishlist_item.product, self.product)


class CategoryAPITest(APITestCase):
    """Tests for Category API"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            full_name='Test User',
            role='CUSTOMER'
        )

        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            full_name='Admin User',
            role='ADMIN',
            is_staff=True
        )

        self.parent_category = Category.objects.create(
            name='Furniture',
            slug='furniture',
            description='All furniture items'
        )

        self.child_category = Category.objects.create(
            name='Chairs',
            slug='chairs',
            description='All types of chairs',
            parent=self.parent_category
        )

        self.client = APIClient()
        self.category_url = reverse('products:category-list')
        self.detail_url = reverse('products:category-detail', kwargs={'pk': self.parent_category.id})

    def test_get_categories(self):
        """Test retrieving categories"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.category_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_category_as_admin(self):
        """Test creating category as admin"""
        self.client.force_authenticate(user=self.admin)
        data = {
            'name': 'Tables',
            'slug': 'tables',
            'description': 'All types of tables',
            'parent': self.parent_category.id
        }
        response = self.client.post(self.category_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Tables')
        self.assertEqual(response.data['parent'], self.parent_category.id)

    def test_create_category_as_customer(self):
        """Test creating category as customer (should fail)"""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'Tables',
            'slug': 'tables',
            'description': 'All types of tables'
        }
        response = self.client.post(self.category_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ProductAPITest(APITestCase):
    """Tests for Product API"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            full_name='Test User',
            role='CUSTOMER'
        )

        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            full_name='Admin User',
            role='ADMIN',
            is_staff=True
        )

        self.category = Category.objects.create(
            name='Chairs',
            slug='chairs',
            description='All types of chairs'
        )

        self.product = Product.objects.create(
            name='Ergonomic Chair',
            slug='ergonomic-chair',
            description='A comfortable ergonomic chair',
            price=Decimal('199.99'),
            category=self.category,
            sku='EC001',
            is_active=True
        )

        self.client = APIClient()
        self.product_url = reverse('products:product-list')
        self.detail_url = reverse('products:product-detail', kwargs={'pk': self.product.id})

    def test_get_products(self):
        """Test retrieving products"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.product_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_product_as_admin(self):
        """Test creating product as admin"""
        self.client.force_authenticate(user=self.admin)
        data = {
            'name': 'Office Desk',
            'slug': 'office-desk',
            'description': 'A spacious office desk',
            'price': '299.99',
            'category': self.category.id,
            'sku': 'OD001',
            'is_active': True
        }
        response = self.client.post(self.product_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Office Desk')
        self.assertEqual(response.data['sku'], 'OD001')

    def test_create_product_as_customer(self):
        """Test creating product as customer (should fail)"""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'Office Desk',
            'slug': 'office-desk',
            'description': 'A spacious office desk',
            'price': '299.99',
            'category': self.category.id,
            'sku': 'OD001'
        }
        response = self.client.post(self.product_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_to_wishlist(self):
        """Test adding product to wishlist"""
        self.client.force_authenticate(user=self.user)
        url = reverse('products:product-add-to-wishlist', kwargs={'pk': self.product.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check wishlist was created
        self.assertTrue(Wishlist.objects.filter(user=self.user).exists())
        wishlist = Wishlist.objects.get(user=self.user)
        self.assertEqual(wishlist.items.count(), 1)
        self.assertEqual(wishlist.items.first().product, self.product)


class WishlistAPITest(APITestCase):
    """Tests for Wishlist API"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            full_name='Test User',
            role='CUSTOMER'
        )

        self.category = Category.objects.create(
            name='Chairs',
            slug='chairs'
        )

        self.product1 = Product.objects.create(
            name='Ergonomic Chair',
            slug='ergonomic-chair',
            description='A comfortable ergonomic chair',
            price=Decimal('199.99'),
            category=self.category,
            sku='EC001',
            is_active=True
        )

        self.product2 = Product.objects.create(
            name='Office Chair',
            slug='office-chair',
            description='Standard office chair',
            price=Decimal('149.99'),
            category=self.category,
            sku='OC001',
            is_active=True
        )

        self.wishlist = Wishlist.objects.create(user=self.user)
        self.wishlist_item = WishlistItem.objects.create(
            wishlist=self.wishlist,
            product=self.product1
        )

        self.client = APIClient()
        self.wishlist_url = reverse('products:wishlist-list')
        self.add_item_url = reverse('products:wishlist-add-item')
        self.remove_item_url = reverse('products:wishlist-remove-item')

    def test_get_wishlist(self):
        """Test retrieving user's wishlist"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.wishlist_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['product'], self.product1.id)

    def test_add_item_to_wishlist(self):
        """Test adding item to wishlist"""
        self.client.force_authenticate(user=self.user)
        data = {'product': self.product2.id}
        response = self.client.post(self.add_item_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 2)

    def test_remove_item_from_wishlist(self):
        """Test removing item from wishlist"""
        self.client.force_authenticate(user=self.user)
        data = {'item_id': self.wishlist_item.id}
        response = self.client.post(self.remove_item_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)