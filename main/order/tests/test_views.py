from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal
from unittest.mock import patch, MagicMock
from order.models import StoreOrder, Cart, CartItem, PaystackWebhook
from mall.models import Store, Category, SubCategories, ProductTypes, Brand, Product, ProductVariant

User = get_user_model()

class ViewOrdersTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='orders@example.com',
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

    def test_list_orders(self):
        order1 = StoreOrder.objects.create(
            buyer=self.user,
            store=self.store,
            total_price=Decimal('25000.00'),
            status='Completed'
        )
        order2 = StoreOrder.objects.create(
            buyer=self.user,
            store=self.store,
            total_price=Decimal('30000.00'),
            status='Pending'
        )
        
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_order_by_reference(self):
        order = StoreOrder.objects.create(
            buyer=self.user,
            store=self.store,
            total_price=Decimal('25000.00'),
            status='Completed'
        )
        
        webhook = PaystackWebhook.objects.create(
            user=self.user,
            store=self.store,
            reference='test_ref_123',
            order=order
        )
        
        response = self.client.get('/api/orders/by-reference/?reference=test_ref_123')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class InitiatePaymentTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='payment@example.com',
            password='test123'
        )
        self.client.force_authenticate(user=self.user)

    @patch('order.views.initiate_payment')
    def test_initiate_order_payment(self, mock_initiate_payment):
        mock_initiate_payment.return_value = {
            'status': True,
            'data': 'https://checkout.paystack.com/test123'
        }
        
        data = {
            'email': 'payment@example.com',
            'amount': 25000,
            'purpose': 'order'
        }
        
        response = self.client.post('/api/initiate-payment/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('data', response.data)

class PaystackViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='paystack@example.com',
            password='test123'
        )
        self.client.force_authenticate(user=self.user)

    @patch('order.views.get_bank_list_paystack')
    def test_get_bank_list(self, mock_get_bank_list):
        mock_get_bank_list.return_value = {
            'status': True,
            'data': [
                {'name': 'Access Bank', 'code': '044'},
                {'name': 'GTBank', 'code': '058'}
            ]
        }
        
        response = self.client.get('/api/paystack/get-banks-list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class PaystackWebhookTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='webhook@example.com',
            password='test123'
        )
        self.store = Store.objects.create(
            name='Test Store',
            owner=self.user
        )

    def test_webhook_get_request(self):
        response = self.client.get('/api/paystack/webhook/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.json())