from django.apps import AppConfig
import os


class MallConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mall'
    
    def ready(self):
        try:
            import mall.signals
        except ImportError:
            pass
