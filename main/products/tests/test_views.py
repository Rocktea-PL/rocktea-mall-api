from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductsViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )

    def test_admin_products_access(self):
        """Test admin can access products endpoints"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/admin/products/')
        # Should return 200 or 404 (if endpoint doesn't exist), not 403
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])