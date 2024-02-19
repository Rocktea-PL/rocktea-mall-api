from django.apps import AppConfig


class MallConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mall'

    def ready(self):
        import mall.signals
