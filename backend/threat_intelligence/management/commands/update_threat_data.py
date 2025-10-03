from django.core.management.base import BaseCommand
from django.utils import timezone
from threat_intelligence.external_api import ThreatIntelligenceUpdater
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update threat intelligence data from external APIs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if data was recently updated',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10000,
            help='Limit number of records to fetch (default: 10000)',
        )
        parser.add_argument(
            '--confidence',
            type=int,
            default=25,
            help='Minimum confidence threshold (default: 25)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting threat intelligence update at {timezone.now()}'
            )
        )

        try:
            updater = ThreatIntelligenceUpdater()
            
            # Update from AbuseIPDB blacklist
            self.stdout.write('Fetching data from AbuseIPDB...')
            success = updater.update_from_abuseipdb_blacklist(
                limit=options['limit'],
                confidence_minimum=options['confidence']
            )
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('Successfully updated threat data from AbuseIPDB')
                )
                
                # Update daily statistics
                self.stdout.write('Updating daily statistics...')
                updater.update_daily_statistics()
                self.stdout.write(
                    self.style.SUCCESS('Successfully updated daily statistics')
                )
                
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to update threat data from AbuseIPDB')
                )
                return
                
        except Exception as e:
            logger.error(f"Error in update_threat_data command: {e}")
            self.stdout.write(
                self.style.ERROR(f'Error updating threat data: {e}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'Threat intelligence update completed at {timezone.now()}'
            )
        )