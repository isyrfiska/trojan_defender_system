import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ThreatIntelligenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'threat_intelligence'
    verbose_name = 'Threat Intelligence'

    def ready(self):
        """Initialize the threat intelligence app."""
        try:
            # Import signals to register them
            from . import signals
            
            # Disable automatic scheduler startup for now to avoid API key issues
            # Start the threat data scheduler in development
            # if self._is_development_server():
            #     from . import tasks
            #     tasks.start_scheduler()
            #     logger.info("Threat intelligence scheduler started")
        except Exception as e:
            logger.error(f"Failed to initialize threat intelligence app: {e}")

    def _is_development_server(self):
        """Check if we're running the development server."""
        import sys
        return 'runserver' in sys.argv or 'daphne' in sys.argv[0]
