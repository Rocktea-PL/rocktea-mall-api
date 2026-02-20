from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from mall.models import (
    CustomUser, Store, Category, SubCategories, ProductTypes, Brand,
    Product, ProductVariant, StoreProductPricing, MarketPlace,
    SavedProduct, Notification, Wallet
)

User = get_user_model()

class CustomUserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_create_user(self):
        user = CustomUser.objects.create_user(password='test123', **self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('test123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        user = CustomUser.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)  # Default admin is staff, not superuser
        self.assertTrue(user.is_admin)  # But has admin access
    
    def test_create_true_superuser(self):
        user = CustomUser.objects.create_true_superuser(
            email='superadmin@example.com',
            password='super123'
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_admin)

    def test_user_str_method(self):
        user = CustomUser.objects.create_user(password='test123', **self.user_data)
        self.assertEqual(str(user), 'Test')

class StoreModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='store@example.com',
            password='test123'
        )

    def test_create_store(self):
        store = Store.objects.create(
            name='Test Store',
            owner=self.user
        )
        self.assertEqual(store.name, 'Test Store')
        self.assertEqual(store.owner, self.user)
        self.assertFalse(store.completed)
        self.assertFalse(store.has_made_payment)

    def test_store_str_method(self):
        store = Store.objects.create(name='Test Store', owner=self.user)
        self.assertEqual(str(store), 'Test Store')

class CategoryModelTest(TestCase):
    def test_create_category(self):
        category = Category.objects.create(name='Electronics')
        self.assertEqual(category.name, 'Electronics')
        self.assertEqual(str(category), 'Electronics')

class ProductModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='product@example.com',
            password='test123'
        )
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

    def test_create_product(self):
        product = Product.objects.create(
            name='iPhone 14',
            description='Latest iPhone model',
            category=self.category,
            subcategory=self.subcategory,
            producttype=self.product_type,
            brand=self.brand,
            quantity=10,
            created_by=self.user
        )
        self.assertEqual(product.name, 'iPhone 14')
        self.assertEqual(product.quantity, 10)
        self.assertEqual(product.sales_count, 0)
        self.assertEqual(product.created_by.id, self.user.id)

class ProductVariantModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='variant@example.com',
            password='test123'
        )
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
            description='Latest iPhone model',
            category=self.category,
            subcategory=self.subcategory,
            producttype=self.product_type,
            brand=self.brand,
            quantity=10,
            created_by=self.user
        )

    def test_create_product_variant(self):
        variant = ProductVariant.objects.create(
            wholesale_price=Decimal('800.00'),
            colors=['Red', 'Blue']
        )
        variant.product.add(self.product)
        self.assertEqual(variant.wholesale_price, Decimal('800.00'))
        self.assertEqual(variant.colors, ['Red', 'Blue'])

class WalletModelTest(TestCase):
    def test_create_wallet(self):
        user = CustomUser.objects.create_user(
            email='wallet@example.com',
            password='test123'
        )
        store = Store.objects.create(
            name='Wallet Store',
            owner=user
        )
        # Get the wallet that was automatically created by the signal
        wallet = Wallet.objects.get(store=store)
        wallet.balance = Decimal('1000.00')
        wallet.account_name = 'Test Account'
        wallet.nuban = '1234567890'
        wallet.bank_code = '001'
        wallet.save()
        
        self.assertEqual(wallet.balance, Decimal('1000.00'))
        self.assertEqual(wallet.account_name, 'Test Account')

class SavedProductModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='saved@example.com',
            password='test123'
        )
        self.store_owner = CustomUser.objects.create_user(
            email='store@example.com',
            password='test123'
        )
        self.store = Store.objects.create(
            name='Test Store',
            owner=self.store_owner
        )
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
            description='Latest iPhone model',
            category=self.category,
            subcategory=self.subcategory,
            producttype=self.product_type,
            brand=self.brand,
            quantity=10,
            created_by=self.user
        )

    def test_create_saved_product(self):
        saved = SavedProduct.objects.create(
            user=self.user,
            product=self.product,
            store=self.store
        )
        self.assertEqual(saved.user, self.user)
        self.assertEqual(saved.product, self.product)
        self.assertEqual(saved.store, self.store)

    def test_unique_constraint(self):
        SavedProduct.objects.create(
            user=self.user,
            product=self.product,
            store=self.store
        )
        with self.assertRaises(Exception):
            SavedProduct.objects.create(
                user=self.user,
                product=self.product,
                store=self.store
            )