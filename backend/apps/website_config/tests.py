from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime

from .models import SiteSettings, HomepageBanner, FAQ, ContactMessage, Promotion

User = get_user_model()


class SiteSettingsModelTest(TestCase):
    """Tests for SiteSettings model"""

    def setUp(self):
        self.settings = SiteSettings.objects.create(
            site_name='Test Furniture Store',
            email='contact@example.com',
            phone='1234567890'
        )

    def test_settings_creation(self):
        """Test settings object is created correctly"""
        self.assertEqual(self.settings.site_name, 'Test Furniture Store')
        self.assertEqual(self.settings.email, 'contact@example.com')
        self.assertEqual(self.settings.phone, '1234567890')


class HomepageBannerModelTest(TestCase):
    """Tests for HomepageBanner model"""

    def setUp(self):
        self.banner = HomepageBanner.objects.create(
            title='New Collection',
            subtitle='Check out our latest furniture',
            image='test.jpg',
            button_text='Shop Now',
            button_link='/products/new',
            display_order=1
        )

    def test_banner_creation(self):
        """Test banner is created correctly"""
        self.assertEqual(self.banner.title, 'New Collection')
        self.assertEqual(self.banner.button_text, 'Shop Now')
        self.assertEqual(self.banner.display_order, 1)
        self.assertTrue(self.banner.is_active)


class FAQModelTest(TestCase):
    """Tests for FAQ model"""

    def setUp(self):
        self.faq = FAQ.objects.create(
            question='How long is delivery?',
            answer='Delivery usually takes 3-5 business days.',
            category='Shipping',
            display_order=1
        )

    def test_faq_creation(self):
        """Test FAQ is created correctly"""
        self.assertEqual(self.faq.question, 'How long is delivery?')
        self.assertEqual(self.faq.category, 'Shipping')
        self.assertTrue(self.faq.is_active)


class ContactMessageModelTest(TestCase):
    """Tests for ContactMessage model"""

    def setUp(self):
        self.message = ContactMessage.objects.create(
            name='John Doe',
            email='john@example.com',
            phone='1234567890',
            subject='Product inquiry',
            message='I have a question about a product.'
        )

    def test_message_creation(self):
        """Test contact message is created correctly"""
        self.assertEqual(self.message.name, 'John Doe')
        self.assertEqual(self.message.email, 'john@example.com')
        self.assertEqual(self.message.status, 'NEW')
        self.assertEqual(str(self.message), 'John Doe: Product inquiry')


class PromotionModelTest(TestCase):
    """Tests for Promotion model"""

    def setUp(self):
        today = timezone.now()
        end_date = today + datetime.timedelta(days=7)

        self.promotion = Promotion.objects.create(
            title='Summer Sale',
            content='Get 20% off on all items',
            promo_type='BANNER',
            start_date=today,
            end_date=end_date
        )

    def test_promotion_creation(self):
        """Test promotion is created correctly"""
        self.assertEqual(self.promotion.title, 'Summer Sale')
        self.assertEqual(self.promotion.promo_type, 'BANNER')
        self.assertTrue(self.promotion.is_active)


class SiteSettingsAPITest(APITestCase):
    """Tests for SiteSettings API"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            full_name='Admin User',
            role='ADMIN',
            is_staff=True
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            full_name='Test User',
            role='CUSTOMER'
        )

        self.settings = SiteSettings.objects.create(
            site_name='Test Furniture Store',
            email='contact@example.com'
        )

        self.client = APIClient()
        self.url = reverse('website_config:settings-list')

    def test_get_settings(self):
        """Test retrieving site settings"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['site_name'], 'Test Furniture Store')

    def test_update_settings_as_admin(self):
        """Test updating settings as admin"""
        self.client.force_authenticate(user=self.admin)
        data = {
            'site_name': 'Updated Store Name',
            'email': 'new@example.com'
        }
        response = self.client.patch(f"{self.url}1/", data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['site_name'], 'Updated Store Name')

    def test_update_settings_as_customer(self):
        """Test updating settings as customer (should fail)"""
        self.client.force_authenticate(user=self.user)
        data = {
            'site_name': 'Hacked Store Name',
            'email': 'hack@example.com'
        }
        response = self.client.patch(f"{self.url}1/", data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class HomepageBannerAPITest(APITestCase):
    """Tests for HomepageBanner API"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            full_name='Admin User',
            role='ADMIN',
            is_staff=True
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            full_name='Test User',
            role='CUSTOMER'
        )

        self.banner = HomepageBanner.objects.create(
            title='Test Banner',
            image='test.jpg',
            display_order=1
        )

        self.client = APIClient()
        self.url = reverse('website_config:banner-list')

    def test_get_banners(self):
        """Test retrieving banners"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_banner_as_admin(self):
        """Test creating banner as admin"""
        self.client.force_authenticate(user=self.admin)
        data = {
            'title': 'New Banner',
            'image': 'new.jpg',
            'display_order': 2
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Banner')

    def test_create_banner_as_customer(self):
        """Test creating banner as customer (should fail)"""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'New Banner',
            'image': 'new.jpg',
            'display_order': 2
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FAQAPITest(APITestCase):
    """Tests for FAQ API"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            full_name='Admin User',
            role='ADMIN',
            is_staff=True
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            full_name='Test User',
            role='CUSTOMER'
        )

        self.faq1 = FAQ.objects.create(
            question='Question 1',
            answer='Answer 1',
            category='Shipping',
            display_order=1
        )

        self.faq2 = FAQ.objects.create(
            question='Question 2',
            answer='Answer 2',
            category='Payment',
            display_order=2
        )

        self.client = APIClient()
        self.url = reverse('website_config:faq-list')
        self.categories_url = reverse('website_config:faq-categories')

    def test_get_faqs(self):
        """Test retrieving FAQs"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_faq_categories(self):
        """Test retrieving FAQ categories"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.categories_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Shipping', response.data)
        self.assertIn('Payment', response.data)

    def test_create_faq_as_admin(self):
        """Test creating FAQ as admin"""
        self.client.force_authenticate(user=self.admin)
        data = {
            'question': 'New Question',
            'answer': 'New Answer',
            'category': 'Returns',
            'display_order': 3
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['question'], 'New Question')


class ContactMessageAPITest(APITestCase):
    """Tests for ContactMessage API"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            full_name='Admin User',
            role='ADMIN',
            is_staff=True
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            full_name='Test User',
            role='CUSTOMER'
        )

        self.message = ContactMessage.objects.create(
            name='John Doe',
            email='john@example.com',
            subject='Test Subject',
            message='This is a test message.'
        )

        self.client = APIClient()
        self.url = reverse('website_config:contact-list')
        self.change_status_url = reverse('website_config:contact-change-status', kwargs={'pk': self.message.id})

    def test_create_message(self):
        """Test creating contact message"""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'subject': 'Question',
            'message': 'I have a question about your products.'
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_messages_as_admin(self):
        """Test listing messages as admin"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_messages_as_customer(self):
        """Test listing messages as customer (should fail)"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_status(self):
        """Test changing message status as admin"""
        self.client.force_authenticate(user=self.admin)
        data = {'status': 'READ'}
        response = self.client.post(self.change_status_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'READ')