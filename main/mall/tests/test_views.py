from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal
from mall.models import (
    Store, Category, SubCategories, ProductTypes, Brand,
    Product, ProductVariant, StoreProductPricing, SavedProduct
)

User = get_user_model()

# Fast test base class
class FastTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create shared test data once
        cls.category = Category.objects.create(name='Electronics')
        cls.subcategory = SubCategories.objects.create(
            name='Phones', 
            category=cls.category
        )
        cls.product_type = ProductTypes.objects.create(
            name='Smartphone',
            subcategory=cls.subcategory
        )
        cls.brand = Brand.objects.create(name='Apple')
        cls.brand.producttype.add(cls.product_type)

class StoreViewSetTest(FastTestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='test123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_store(self):
        category, _ = Category.objects.get_or_create(name='Electronics')
        data = {
            'name': 'Test Store',
            'category': category.id
        }
        response = self.client.post('/rocktea/create/store/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Store.objects.count(), 1)

    def test_list_stores(self):
        Store.objects.create(name='Store 1', owner=self.user)
        
        response = self.client.get('/rocktea/create/store/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class ProductViewSetTest(FastTestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='test123'
        )
        self.client.force_authenticate(user=self.user)

    def test_list_products(self):
        Product.objects.create(
            name='iPhone 14',
            description='Test iPhone 14 description',
            category=self.category,
            subcategory=self.subcategory,
            producttype=self.product_type,
            brand=self.brand,
            quantity=10
        )
        
        response = self.client.get('/rocktea/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_detail(self):
        product = Product.objects.create(
            name='iPhone 14',
            description='Test iPhone 14 description',
            category=self.category,
            subcategory=self.subcategory,
            producttype=self.product_type,
            brand=self.brand,
            quantity=10,
            is_available=True,
            upload_status='Approved'
        )
        
        response = self.client.get(f'/rocktea/products/{product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'iPhone 14')

class CategoryViewSetTest(FastTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_categories(self):
        Category.objects.create(name='Health & Beauty')
        
        response = self.client.get('/rocktea/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class WishlistViewSetTest(FastTestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='test123'
        )
        self.store_owner = User.objects.create_user(
            email='store@example.com',
            password='test123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.store = Store.objects.create(
            name='Test Store',
            owner=self.store_owner
        )
        self.product = Product.objects.create(
            name='iPhone 14',
            description='Test iPhone 14 description',
            category=self.category,
            subcategory=self.subcategory,
            producttype=self.product_type,
            brand=self.brand,
            quantity=10
        )

    def test_save_product(self):
        data = {
            'product_id': self.product.id,
            'store_id': self.store.id
        }
        response = self.client.post('/rocktea/wishlist/save/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SavedProduct.objects.count(), 1)

    def test_unsave_product(self):
        SavedProduct.objects.create(
            user=self.user,
            product=self.product,
            store=self.store
        )
        
        data = {
            'product_id': self.product.id,
            'store_id': self.store.id
        }
        response = self.client.delete('/rocktea/wishlist/unsave/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SavedProduct.objects.count(), 0)

    def test_list_saved_products(self):
        SavedProduct.objects.create(
            user=self.user,
            product=self.product,
            store=self.store
        )
        
        response = self.client.get('/rocktea/wishlist/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class BestSellingProductViewTest(FastTestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='store@example.com',
            password='test123'
        )
        self.store = Store.objects.create(
            name='Test Store',
            owner=self.user
        )

    def test_best_selling_products(self):
        product1 = Product.objects.create(
            name='iPhone 14',
            description='Test iPhone 14 description',
            category=self.category,
            subcategory=self.subcategory,
            producttype=self.product_type,
            brand=self.brand,
            quantity=10,
            sales_count=100
        )
        product2 = Product.objects.create(
            name='iPhone 13',
            description='Test iPhone 13 description',
            category=self.category,
            subcategory=self.subcategory,
            producttype=self.product_type,
            brand=self.brand,
            quantity=5,
            sales_count=50
        )
        
        # Create marketplace entries
        from mall.models import MarketPlace
        MarketPlace.objects.create(product=product1, store=self.store)
        MarketPlace.objects.create(product=product2, store=self.store)
        
        response = self.client.get(f'/mall/best_selling?store={self.store.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)