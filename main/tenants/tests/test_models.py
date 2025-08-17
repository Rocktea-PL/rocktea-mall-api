from django.test import TestCase

class TenantsTest(TestCase):
    def test_tenants_app_exists(self):
        """Test that tenants app is properly configured"""
        from tenants import apps
        self.assertEqual(apps.TenantsConfig.name, 'tenants')