from django.apps import AppConfig


class StatuspageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'statuspage'
    
    def ready(self):
        import statuspage.signals
