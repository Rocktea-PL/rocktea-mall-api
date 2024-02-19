import json
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from mall.models import CustomUser
from django.core.files.uploadedfile import SimpleUploadedFile


class CreateStoreOwnerTests(TestCase):
   def setUp(self):
      self.client = APIClient()

   def test_create_store_owner(self):
      # Define the data to be sent in the request
      data = {
         "first_name": "John",
         "last_name": "Doe",
         # "username": "johndoe",
         "email": "johndoe@example.com",
         "contact": "+2349018299384",
         # "profile_image": "example.jpg",
         "is_store_owner": True,
         "password": "SecurePassword123",
         # "shipping_address": "123 Main St, City" 
      }
      
      # Create a simple image file for testing
      # image_content = b"example image content"
      # image = SimpleUploadedFile("example.jpg", image_content, content_type="image/jpeg")

      # # Add the file to the data as part of the 'profile_image' field
      # data['profile_image'] = image

      # Send a POST request to create a new store owner
      response = self.client.post(
         '/rocktea/storeowner/', json.dumps(data), content_type='application/json')

      # Assert the response status code
      self.assertEqual(response.status_code, status.HTTP_201_CREATED)

      # Assert that the store owner was created in the database
      # self.assertTrue(CustomUser.objects.filter(username="johndoe").exists())

      # You may want to further assert the response data, for example:
      response_data = response.json()
      # self.assertEqual(response_data["username"], "johndoe")
      self.assertTrue(response_data["is_store_owner"])

   def test_invalid_password(self):
      # Define data with an invalid password
      data = {
         "first_name": "John",
         "last_name": "Doe",
         # "username": "johndoe",
         "email": "johndoe@example.com",
         "contact": "+2348028277364",
         # "profile_image": "example.jpg",
         "is_store_owner": True,
         "password": "weakpassword",  # Invalid password
         "shipping_address": "123 Main St, City"
      }

      # Send a POST request with an invalid password
      response = self.client.post(
         '/rocktea/storeowner/', json.dumps(data), content_type='application/json')

      # Assert the response status code
      self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

      # Assert the error message in the response
      response_data = response.json()
      self.assertIn("error", response_data)

      # Assert that the store owner was not created in the database
      # self.assertFalse(CustomUser.objects.filter(last_name=="Doe").exists()) 
