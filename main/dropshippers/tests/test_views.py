from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal
from mall.models import Store, Category
from order.models import StoreOrder

User = get_user_model()

class DropshipperDashboardTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='dropshipper@example.com',
            password='test123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.store = Store.objects.create(
            name='Dropshipper Store',
            owner=self.user,
            completed=True,
            has_made_payment=True
        )

    def test_dashboard_access_authenticated(self):
        response = self.client.get('/api/dropshippers/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_access_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/dropshippers/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class DropshipperStoreTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='dropshipper@example.com',
            password='test123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_store(self):
        data = {
            'name': 'New Dropshipper Store',
            'category': 'Electronics'
        }
        
        response = self.client.post('/api/dropshippers/stores/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Store.objects.filter(name='New Dropshipper Store').exists())

    def test_list_user_stores(self):
        Store.objects.create(name='Store 1', owner=self.user)
        
        # Create another user's store (should not appear)
        other_user = User.objects.create_user(
            email='other@example.com',
            password='test123'
        )
        Store.objects.create(name='Other Store', owner=other_user)
        
        response = self.client.get('/api/dropshippers/stores/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class DropshipperOrdersTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.dropshipper = User.objects.create_user(
            email='dropshipper@example.com',
            password='test123'
        )
        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='test123'
        )
        self.client.force_authenticate(user=self.dropshipper)
        
        self.store = Store.objects.create(
            name='Dropshipper Store',
            owner=self.dropshipper
        )

    def test_list_store_orders(self):
        # Create orders for this store
        order1 = StoreOrder.objects.create(
            buyer=self.customer,
            store=self.store,
            total_price=Decimal('25000.00'),
            status='Completed'
        )
        order2 = StoreOrder.objects.create(
            buyer=self.customer,
            store=self.store,
            total_price=Decimal('30000.00'),
            status='Pending'
        )
        
        response = self.client.get('/api/dropshippers/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_order_status(self):
        order = StoreOrder.objects.create(
            buyer=self.customer,
            store=self.store,
            total_price=Decimal('25000.00'),
            status='Pending'
        )
        
        data = {'status': 'Enroute'}
        
        response = self.client.patch(f'/api/dropshippers/orders/{order.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        order.refresh_from_db()
        self.assertEqual(order.status, 'Enroute')

class AdminDropshipperCreationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_admin_create_dropshipper_account(self):
        """Test admin can create dropshipper accounts"""
        data = {
            'email': 'newdropshipper@example.com',
            'password': 'secure123',
            'first_name': 'New',
            'last_name': 'Dropshipper',
            'is_store_owner': True
        }
        
        response = self.client.post('/rocktea/storeowner/', data)
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        
        # Verify user was created
        self.assertTrue(User.objects.filter(email='newdropshipper@example.com').exists())

class DropshipperPermissionsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='test123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='test123'
        )
        
        self.store1 = Store.objects.create(
            name='User1 Store',
            owner=self.user1
        )
        self.store2 = Store.objects.create(
            name='User2 Store',
            owner=self.user2
        )

    def test_cannot_access_other_user_store(self):
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(f'/api/dropshippers/stores/{self.store2.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_update_other_user_store(self):
        self.client.force_authenticate(user=self.user1)
        
        data = {'name': 'Hacked Store'}
        response = self.client.patch(f'/api/dropshippers/stores/{self.store2.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify store name wasn't changed
        self.store2.refresh_from_db()
        self.assertEqual(self.store2.name, 'User2 Store')