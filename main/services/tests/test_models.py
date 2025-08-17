from django.test import TestCase

class ServicesTest(TestCase):
    def test_services_app_exists(self):
        """Test that services app is properly configured"""
        from services import apps
        self.assertEqual(apps.ServicesConfig.name, 'services')