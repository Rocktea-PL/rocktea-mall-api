from django.test import TestCase

class DashboardsTest(TestCase):
    def test_dashboards_app_exists(self):
        """Test that dashboards app is properly configured"""
        from dashboards import apps
        self.assertEqual(apps.DashboardsConfig.name, 'dashboards')