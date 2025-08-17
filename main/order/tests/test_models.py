from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from order.models import (
    StoreOrder, OrderItems, Cart, CartItem, State,
    PaymentHistory, PaystackWebhook, WithdrawalRecord
)
from mall.models import (
    Store, Category, SubCategories, ProductTypes, Brand,
    Product, ProductVariant, Wallet
)

User = get_user_model()

class StateModelTest(TestCase):
    def test_create_state(self):
        state = State.objects.create(
            state='Lagos',
            delivery_fee=Decimal('1500.00'),
            zip_code=100001
        )
        self.assertEqual(state.state, 'Lagos')
        self.assertEqual(state.delivery_fee, Decimal('1500.00'))
        self.assertEqual(str(state), 'Lagos')

class StoreOrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='buyer@example.com',
            password='test123'
        )
        self.store_owner = User.objects.create_user(
            email='store@example.com',
            password='test123'
        )
        self.store = Store.objects.create(
            name='Test Store',
            owner=self.store_owner
        )
        self.state = State.objects.create(
            state='Lagos',
            delivery_fee=Decimal('1500.00'),
            zip_code=100001
        )

    def test_create_order(self):
        order = StoreOrder.objects.create(
            buyer=self.user,
            store=self.store,
            total_price=Decimal('25000.00'),
            status='Pending',
            delivery_location='123 Test Street',
            state=self.state
        )
        self.assertEqual(order.buyer, self.user)
        self.assertEqual(order.store, self.store)
        self.assertEqual(order.status, 'Pending')
        self.assertIsNotNone(order.order_sn)
        self.assertIsNotNone(order.delivery_code)

    def test_order_sn_generation(self):
        order1 = StoreOrder.objects.create(
            buyer=self.user,
            store=self.store,
            total_price=Decimal('25000.00')
        )
        order2 = StoreOrder.objects.create(
            buyer=self.user,
            store=self.store,
            total_price=Decimal('30000.00')
        )
        self.assertNotEqual(order1.order_sn, order2.order_sn)
        self.assertEqual(len(order1.order_sn), 5)

class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='cart@example.com',
            password='test123'
        )
        self.store_owner = User.objects.create_user(
            email='store@example.com',
            password='test123'
        )
        self.store = Store.objects.create(
            name='Test Store',
            owner=self.store_owner
        )

    def test_create_cart(self):
        cart = Cart.objects.create(
            user=self.user,
            store=self.store,
            price=Decimal('0.00')
        )
        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.store, self.store)
        self.assertEqual(cart.price, Decimal('0.00'))

class PaystackWebhookModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='webhook@example.com',
            password='test123'
        )
        self.store = Store.objects.create(
            name='Test Store',
            owner=self.user
        )

    def test_create_webhook(self):
        webhook = PaystackWebhook.objects.create(
            user=self.user,
            store=self.store,
            reference='test_ref_123',
            total_price=Decimal('25000.00'),
            status='Pending',
            purpose='order'
        )
        self.assertEqual(webhook.reference, 'test_ref_123')
        self.assertEqual(webhook.status, 'Pending')
        self.assertEqual(str(webhook), 'test_ref_123')

class WithdrawalRecordModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='withdrawal@example.com',
            password='test123'
        )
        self.store = Store.objects.create(
            name='Test Store',
            owner=self.user
        )
        self.wallet = Wallet.objects.create(
            store=self.store,
            balance=Decimal('10000.00'),
            account_name='Test Account',
            nuban='1234567890',
            bank_code='001'
        )

    def test_create_withdrawal_record(self):
        withdrawal = WithdrawalRecord.objects.create(
            store=self.store,
            wallet=self.wallet,
            amount=Decimal('5000.00'),
            recipient_code='RCP_test123',
            status='pending'
        )
        self.assertEqual(withdrawal.amount, Decimal('5000.00'))
        self.assertEqual(withdrawal.status, 'pending')
        self.assertEqual(str(withdrawal), 'Test Store - 5000.00 - pending')