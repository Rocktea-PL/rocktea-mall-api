from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from order.models import Cart, CartItem
from order.cart_service import CartService
from mall.models import Store, Product, ProductVariant, StoreProductPricing, Category

User = get_user_model()

class CartServiceTestCase(TestCase):
    def setUp(self):
        from mall.models import SubCategories, ProductTypes, Brand
        
        # Create test data
        self.user = User.objects.create_user(email='test@example.com', password='testpass')
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
        
        # Create store pricing
        self.pricing = StoreProductPricing.objects.create(
            product=self.product, 
            store=self.store, 
            retail_price=Decimal('150.00')
        )
        
        # Create cart
        self.cart = Cart.objects.create(user=self.user, store=self.store, price=Decimal('0.00'))

    def test_get_item_price(self):
        """Test correct price calculation"""
        price = CartService.get_item_price(self.product.id, self.store, quantity=2)
        self.assertEqual(price, Decimal('300.00'))  # 150 * 2

    def test_add_new_item(self):
        """Test adding new item to cart"""
        item = CartService.add_or_update_item(
            self.cart, self.product.id, self.variant.id, 2, self.store
        )
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, Decimal('300.00'))

    def test_update_existing_item(self):
        """Test updating existing item quantity"""
        # Add initial item
        CartService.add_or_update_item(self.cart, self.product.id, self.variant.id, 1, self.store)
        
        # Add more of same item
        item = CartService.add_or_update_item(self.cart, self.product.id, self.variant.id, 2, self.store)
        
        self.assertEqual(item.quantity, 3)  # 1 + 2
        self.assertEqual(item.price, Decimal('450.00'))  # 150 * 3

    def test_update_cart_total(self):
        """Test cart total calculation"""
        CartService.add_or_update_item(self.cart, self.product.id, self.variant.id, 2, self.store)
        total = CartService.update_cart_total(self.cart)
        
        self.assertEqual(total, Decimal('300.00'))
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.price, Decimal('300.00'))

    def test_update_item_quantity(self):
        """Test updating item quantity"""
        item = CartService.add_or_update_item(self.cart, self.product.id, self.variant.id, 2, self.store)
        
        # Update quantity
        updated_item = CartService.update_item_quantity(item, 5)
        
        self.assertEqual(updated_item.quantity, 5)
        self.assertEqual(updated_item.price, Decimal('750.00'))  # 150 * 5

    def test_remove_item_with_zero_quantity(self):
        """Test item removal when quantity is 0"""
        item = CartService.add_or_update_item(self.cart, self.product.id, self.variant.id, 2, self.store)
        
        # Set quantity to 0
        result = CartService.update_item_quantity(item, 0)
        
        self.assertIsNone(result)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())