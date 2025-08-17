from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()

class UserRegistrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration_success(self):
        data = {
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_user_registration_duplicate_email(self):
        User.objects.create_user(
            email='existing@example.com',
            password='test123'
        )
        
        data = {
            'email': 'existing@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserLoginTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='login@example.com',
            password='testpass123'
        )

    def test_user_login_success(self):
        data = {
            'email': 'login@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_user_login_invalid_credentials(self):
        data = {
            'email': 'login@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class UserProfileTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='profile@example.com',
            password='testpass123',
            first_name='Profile',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)

    def test_get_user_profile(self):
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'profile@example.com')

    def test_update_user_profile(self):
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = self.client.patch('/api/auth/profile/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

class PasswordChangeTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='password@example.com',
            password='oldpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self):
        data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123'
        }
        
        response = self.client.post('/api/auth/change-password/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    def test_change_password_wrong_old_password(self):
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass123'
        }
        
        response = self.client.post('/api/auth/change-password/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)