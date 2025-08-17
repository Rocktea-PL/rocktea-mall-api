from django.test import TestCase

class AdminOrdersTest(TestCase):
    def test_admin_orders_app_exists(self):
        """Test that admin_orders app is properly configured"""
        from admin_orders import apps
        self.assertEqual(apps.AdminOrdersConfig.name, 'admin_orders')