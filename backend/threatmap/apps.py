from django.apps import AppConfig


class ThreatmapConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'threatmap'
    
    def ready(self):
        import threatmap.signals  # noqa