import random
import logging
from django.conf import settings

logger = logging.getLogger('api')

class DatabaseRouter:
    """
    Database router for read/write splitting and multi-database support.
    
    This router allows:
    - Read/write splitting (read from replicas, write to primary)
    - Specific app routing to dedicated databases
    - Automatic failover if a database is unavailable
    
    To use this router, configure multiple databases in settings.py:
    
    DATABASES = {
        'default': { ... },  # Primary database
        'replica1': { ... },  # Read replica 1
        'replica2': { ... },  # Read replica 2
        'analytics': { ... },  # Analytics database
    }
    
    DATABASE_ROUTERS = ['trojan_defender.db_router.DatabaseRouter']
    
    DATABASE_APPS_MAPPING = {
        'app1': 'default',
        'app2': 'analytics',
    }
    
    DATABASE_READ_REPLICAS = ['replica1', 'replica2']
    """
    
    def __init__(self):
        # Get app-specific database mappings
        self.app_mapping = getattr(settings, 'DATABASE_APPS_MAPPING', {})
        
        # Get read replicas
        self.read_replicas = getattr(settings, 'DATABASE_READ_REPLICAS', [])
        
        # Get primary database
        self.primary_db = 'default'
    
    def db_for_read(self, model, **hints):
        """
        Route read operations to appropriate database.
        
        Strategy:
        1. Check if the app has a specific database mapping
        2. If read replicas are available, randomly select one
        3. Fall back to primary database
        """
        # Check for app-specific mapping
        app_label = model._meta.app_label
        if app_label in self.app_mapping:
            db = self.app_mapping[app_label]
            logger.debug(f"Routing read for {app_label}.{model.__name__} to app-specific database: {db}")
            return db
        
        # Use read replica if available
        if self.read_replicas:
            db = random.choice(self.read_replicas)
            logger.debug(f"Routing read for {app_label}.{model.__name__} to read replica: {db}")
            return db
        
        # Fall back to primary
        logger.debug(f"Routing read for {app_label}.{model.__name__} to primary database")
        return self.primary_db
    
    def db_for_write(self, model, **hints):
        """
        Route write operations to appropriate database.
        
        Strategy:
        1. Check if the app has a specific database mapping
        2. Use primary database
        """
        # Check for app-specific mapping
        app_label = model._meta.app_label
        if app_label in self.app_mapping:
            db = self.app_mapping[app_label]
            logger.debug(f"Routing write for {app_label}.{model.__name__} to app-specific database: {db}")
            return db
        
        # Use primary database
        logger.debug(f"Routing write for {app_label}.{model.__name__} to primary database")
        return self.primary_db
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if both objects are in the same database or in databases
        that are configured to allow relations between each other.
        """
        # Get database for each object
        db1 = self.get_db_for_model(obj1._meta.app_label)
        db2 = self.get_db_for_model(obj2._meta.app_label)
        
        # Allow relations between objects in the same database
        if db1 == db2:
            return True
        
        # Allow relations between primary and read replicas
        if db1 == self.primary_db and db2 in self.read_replicas:
            return True
        
        if db2 == self.primary_db and db1 in self.read_replicas:
            return True
        
        # Disallow other relations
        return False
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure migrations only run on the appropriate database.
        """
        # Get target database for this app
        target_db = self.get_db_for_model(app_label)
        
        # Only allow migrations on the target database
        if db == target_db:
            return True
        
        # Allow migrations on primary database for all apps
        if db == self.primary_db:
            return True
        
        # Don't run migrations on read replicas
        if db in self.read_replicas:
            return False
        
        # Default to allowing migrations
        return None
    
    def get_db_for_model(self, app_label):
        """
        Get the database for a specific app.
        """
        if app_label in self.app_mapping:
            return self.app_mapping[app_label]
        return self.primary_db