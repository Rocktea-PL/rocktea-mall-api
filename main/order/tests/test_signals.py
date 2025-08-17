from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from unittest.mock import patch
from order.models import StoreOrder, OrderItems
from order.signals import send_order_completion_email
from mall.models import Store, Category, SubCategories, ProductTypes, Brand, Product, ProductVariant, StoreProductPricing

User = get_user_model()

class OrderSignalsTest(TestCase):
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
            category=self.category,
            subcategory=self.subcategory,
            producttype=self.product_type,
            brand=self.brand,
            quantity=10
        )
        self.variant = ProductVariant.objects.create(
            wholesale_price=Decimal('800.00')
        )
        self.variant.product.add(self.product)
        
        # Create store pricing
        StoreProductPricing.objects.create(
            store=self.store,
            product=self.product,
            retail_price=Decimal('1000.00')
        )

    @patch('order.signals.send_email_task')
    def test_order_completion_email_signal(self, mock_send_email):
        # Create order with Completed status
        order = StoreOrder.objects.create(
            buyer=self.user,
            store=self.store,
            total_price=Decimal('2000.00'),
            status='Completed',
            delivery_location='123 Test Street'
        )
        
        # Create order item
        OrderItems.objects.create(
            userorder=order,
            product=self.product,
            product_variant=self.variant,
            quantity=2
        )
        
        # Trigger signal manually
        send_order_completion_email(StoreOrder, order, created=False)
        
        # Verify email task was called
        mock_send_email.delay.assert_called_once()

    @patch('order.signals.send_email_task')
    def test_order_completion_email_not_sent_for_pending(self, mock_send_email):
        # Create order with Pending status
        order = StoreOrder.objects.create(
            buyer=self.user,
            store=self.store,
            total_price=Decimal('2000.00'),
            status='Pending'
        )
        
        # Trigger signal manually
        send_order_completion_email(StoreOrder, order, created=False)
        
        # Verify email task was NOT called
        mock_send_email.delay.assert_not_called()