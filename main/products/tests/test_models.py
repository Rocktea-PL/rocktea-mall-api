from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductsAppTest(TestCase):
    def test_products_app_exists(self):
        """Test that products app is properly configured"""
        from products import apps
        self.assertEqual(apps.ProductsConfig.name, 'products')