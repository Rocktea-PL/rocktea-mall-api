from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import CustomUser
# Create your tests here.

class TestCustomerSignUp(TestCase):
   def setUp(cls):
      self.client = APIClient()
      self.user_data = {
         "email": "user123@example.com",
         "first_name": "John",
         "last_name": "Doe",
         "contact": "+1234567890",
         "is_store_owner": true,
         "is_consumer": false,
         "password": "securepassword123",
         "associated_domain": "52bad6dd-1f01-4216-925e-c660adb9b91f",
         # "profile_image": "path/to/profile/image.jpg"
         }
      self.url = reverse('user')
   
   def test_create_store_owner(self):
      response = self.client.post(self.url, self.user_data, format='json')
      self.assertEqual(response.status_code, status.HTTP_201_CREATED)
      