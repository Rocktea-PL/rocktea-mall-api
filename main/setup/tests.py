from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from decimal import Decimal
from setup.tasks import send_email_task, send_order_completion_email_task
from mall.models import Store
from order.models import StoreOrder, OrderItems
from mall.models import (
    Category, SubCategories, ProductTypes, Brand,
    Product, ProductVariant, StoreProductPricing
)

User = get_user_model()

class EmailTaskTest(TestCase):
    @patch('setup.tasks.requests.post')
    @patch('setup.tasks.render_to_string')
    @patch('setup.tasks.strip_tags')
    def test_send_email_task_success(self, mock_strip_tags, mock_render, mock_post):
        mock_render.return_value = '<html>Test Email</html>'
        mock_strip_tags.return_value = 'Test Email'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'messageId': 'test123'}
        mock_post.return_value = mock_response
        
        result = send_email_task(
            recipient_email='test@example.com',
            template_name='test_template.html',
            context={'name': 'Test'},
            subject='Test Subject'
        )
        
        self.assertIsNotNone(result)
        mock_post.assert_called_once()

    @patch('setup.tasks.requests.post')
    def test_send_email_task_failure(self, mock_post):
        mock_post.side_effect = Exception('API Error')
        
        result = send_email_task(
            recipient_email='test@example.com',
            template_name='test_template.html',
            context={'name': 'Test'},
            subject='Test Subject'
        )
        
        self.assertIsNone(result)

class OrderCompletionEmailTaskTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='buyer@example.com',
            password='test123',
            first_name='John',
            last_name='Doe'
        )
        self.store_owner = User.objects.create_user(
            email='store@example.com',
            password='test123'
        )
        self.store = Store.objects.create(
            name='Test Store',
            owner=self.store_owner
        )
        
        # Create product hierarchy
        self.category = Category.objects.create(name='Electronics')
        self.subcategory = SubCategories.objects.create(
            name='Phones', 
            category=self.category
        )
        self.product_type = ProductTypes.objects.create(
            name='Smartphone',
            subcategory=self.subcategory
        )
        self.brand = Brand.objects.create(name='Apple')
        self.brand.producttype.add(self.product_type)
        self.product = Product.objects.create(
            name='iPhone 14',
            description='Test iPhone 14 description',
            category=self.category,
            subcategory=self.subcategory,
            producttype=self.product_type,
            brand=self.brand,
            quantity=10
        )
        self.variant = ProductVariant.objects.create(
            wholesale_price=Decimal('800.00'),
            colors=['Red', 'Blue']
        )
        self.variant.product.add(self.product)
        
        # Create store pricing
        StoreProductPricing.objects.create(
            store=self.store,
            product=self.product,
            retail_price=Decimal('1000.00')
        )
        
        self.order = StoreOrder.objects.create(
            buyer=self.user,
            store=self.store,
            total_price=Decimal('2000.00'),
            status='Completed'
        )
        
        OrderItems.objects.create(
            userorder=self.order,
            product=self.product,
            product_variant=self.variant,
            quantity=2
        )

    @patch('setup.tasks.send_email_task')
    def test_send_order_completion_email_task_success(self, mock_send_email):
        mock_send_email.return_value = {'messageId': 'test123'}
        
        result = send_order_completion_email_task(self.order.id)
        
        self.assertIn('Email sent', result)
        mock_send_email.assert_called_once()

    def test_send_order_completion_email_task_nonexistent_order(self):
        result = send_order_completion_email_task('nonexistent-id')
        self.assertIn('Order not found', result)

class CeleryConfigTest(TestCase):
    def test_celery_app_exists(self):
        from setup.celery import app
        self.assertIsNotNone(app)
        self.assertEqual(app.main, 'setup')