from django.core.management.base import BaseCommand
from scanner.ml_models import ThreatPredictionEngine
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Train machine learning models for threat prediction'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            choices=['all', 'network', 'threat'],
            default='all',
            help='Which model to train'
        )
        parser.add_argument(
            '--lookback-days',
            type=int,
            default=30,
            help='Number of days of historical data to use'
        )
    
    def handle(self, *args, **options):
        engine = ThreatPredictionEngine()
        model_type = options['model']
        lookback_days = options['lookback_days']
        
        self.stdout.write(f"Training ML models with {lookback_days} days of data...")
        
        results = {}
        
        if model_type in ['all', 'network']:
            self.stdout.write("Training network anomaly detector...")
            results['network'] = engine.train_network_anomaly_detector(lookback_days)
            
        if model_type in ['all', 'threat']:
            self.stdout.write("Training threat classifier...")
            results['threat'] = engine.train_threat_classifier(lookback_days)
        
        # Report results
        for model_name, success in results.items():
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ {model_name} model trained successfully")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ Failed to train {model_name} model")
                )
        
        self.stdout.write("ML model training completed.")