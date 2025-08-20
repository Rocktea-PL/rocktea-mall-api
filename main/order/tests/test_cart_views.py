from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal
from order.models import Cart, CartItem
from mall.models import Store, Product, ProductVariant, StoreProductPricing, Category

User = get_user_model()

class CartViewTestCase(TestCase):
    def setUp(self):
        from mall.models import SubCategories, ProductTypes, Brand
        
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.category = Category.objects.create(name='Electronics')
        self.subcategory = SubCategories.objects.create(name='Phones', category=self.category)
        self.producttype = ProductTypes.objects.create(name='Smartphone', subcategory=self.subcategory)
        self.brand = Brand.objects.create(name='TestBrand')
        self.brand.producttype.add(self.producttype)
        
        self.store = Store.objects.create(name='Test Store', owner=self.user, category=self.category)
        self.product = Product.objects.create(
            name='Test Product',
            description='Test description', 
            quantity=10, 
            category=self.category,
            subcategory=self.subcategory,
            producttype=self.producttype,
            brand=self.brand
        )
        self.variant = ProductVariant.objects.create(size='Large', colors=['Red'], wholesale_price=Decimal('100.00'))
        self.variant.product.add(self.product)
        
        StoreProductPricing.objects.create(
            product=self.product, 
            store=self.store, 
            retail_price=Decimal('150.00')
        )

    def test_add_to_cart(self):
        """Test adding products to cart"""
        data = {
            'products': [{
                'id': self.product.id,
                'variant': self.variant.id,
                'quantity': 2
            }]
        }
        
        # Mock the store domain processing
        from unittest.mock import patch
        with patch('order.views.get_store_domain') as mock_get_store:
            mock_get_store.return_value = str(self.store.id)
            with patch('order.views.handler.process_request') as mock_process:
                mock_process.return_value = self.store.id
                
                response = self.client.post('/rocktea/cart/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check cart was created with correct total
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.price, Decimal('300.00'))  # 150 * 2

    def test_update_cart_item_quantity(self):
        """Test updating cart item quantity"""
        # Create cart item
        cart = Cart.objects.create(user=self.user, store=self.store)
        item = CartItem.objects.create(
            cart=cart, 
            product=self.product, 
            product_variant=self.variant,
            quantity=2,
            price=Decimal('300.00')
        )
        
        # Update quantity
        response = self.client.patch(f'/rocktea/cart-item/{item.id}/', 
                                   {'quantity': 5}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check item was updated
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)
        self.assertEqual(item.price, Decimal('750.00'))  # 150 * 5