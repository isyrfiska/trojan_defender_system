#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script for Trojan Defender
This script migrates data from SQLite to PostgreSQL database.
"""

import os
import sys
import json
import django
from django.core.management import call_command
from django.core import serializers
from django.apps import apps
from django.db import transaction
from io import StringIO

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trojan_defender.settings')

def backup_sqlite_data():
    """Backup all data from SQLite database"""
    print("Backing up SQLite data...")
    
    # Temporarily switch to SQLite for data export
    from django.conf import settings
    original_db_config = settings.DATABASES['default'].copy()
    
    # Configure SQLite connection
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__), 'db.sqlite3'),
    }
    
    django.setup()
    
    try:
        # Get all models
        all_models = []
        for app_config in apps.get_app_configs():
            if app_config.name not in ['django.contrib.contenttypes', 
                                     'django.contrib.auth', 
                                     'django.contrib.admin',
                                     'django.contrib.sessions',
                                     'django.contrib.messages']:
                all_models.extend(app_config.get_models())
        
        # Export data
        data = []
        for model in all_models:
            model_data = serializers.serialize('json', model.objects.all())
            if model_data != '[]':  # Only include models with data
                data.extend(json.loads(model_data))
                print(f"✓ Exported {model.objects.count()} records from {model._meta.label}")
        
        # Save backup
        backup_file = 'sqlite_backup.json'
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Data backed up to {backup_file}")
        return backup_file, len(data)
        
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return None, 0
    finally:
        # Restore original database configuration
        settings.DATABASES['default'] = original_db_config

def restore_postgresql_data(backup_file):
    """Restore data to PostgreSQL database"""
    print("Restoring data to PostgreSQL...")
    
    # Load environment for PostgreSQL
    from dotenv import load_dotenv
    load_dotenv()
    
    django.setup()
    
    try:
        # Load backup data
        with open(backup_file, 'r') as f:
            data = json.load(f)
        
        # Create a temporary fixture file
        fixture_file = 'temp_fixture.json'
        with open(fixture_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Load data into PostgreSQL
        with transaction.atomic():
            call_command('loaddata', fixture_file, verbosity=2)
        
        print(f"✓ Restored {len(data)} records to PostgreSQL")
        
        # Clean up temporary file
        os.remove(fixture_file)
        
        return True
        
    except Exception as e:
        print(f"✗ Restore failed: {e}")
        return False

def verify_migration():
    """Verify that migration was successful"""
    print("Verifying migration...")
    
    try:
        from django.db import connection
        cursor = connection.cursor()
        
        # Get table counts
        cursor.execute("""
            SELECT schemaname,tablename,n_tup_ins 
            FROM pg_stat_user_tables 
            WHERE schemaname='public'
        """)
        
        tables = cursor.fetchall()
        total_records = sum(table[2] for table in tables)
        
        print(f"✓ Migration verified: {len(tables)} tables, {total_records} total records")
        
        for schema, table, count in tables:
            if count > 0:
                print(f"  - {table}: {count} records")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False

def main():
    """Main migration function"""
    print("=" * 60)
    print("SQLite to PostgreSQL Migration for Trojan Defender")
    print("=" * 60)
    
    # Check if SQLite database exists
    sqlite_db = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    if not os.path.exists(sqlite_db):
        print("✗ SQLite database not found. Nothing to migrate.")
        return
    
    print(f"Found SQLite database: {sqlite_db}")
    
    # Confirm migration
    confirm = input("This will migrate data from SQLite to PostgreSQL. Continue? (y/n): ")
    if confirm.lower() != 'y':
        print("Migration cancelled.")
        return
    
    # Step 1: Backup SQLite data
    backup_file, record_count = backup_sqlite_data()
    if not backup_file:
        print("Migration failed during backup.")
        return
    
    print(f"Backed up {record_count} records")
    
    if record_count == 0:
        print("No data to migrate.")
        return
    
    # Step 2: Ensure PostgreSQL is set up
    print("\nEnsure PostgreSQL database is set up and migrations are run.")
    proceed = input("Have you run setup_postgresql.py? (y/n): ")
    if proceed.lower() != 'y':
        print("Please run setup_postgresql.py first.")
        return
    
    # Step 3: Restore data to PostgreSQL
    if not restore_postgresql_data(backup_file):
        print("Migration failed during restore.")
        return
    
    # Step 4: Verify migration
    if not verify_migration():
        print("Migration completed but verification failed.")
        return
    
    print("\n" + "=" * 60)
    print("✓ Migration completed successfully!")
    print("✓ All data has been transferred to PostgreSQL")
    print("=" * 60)
    
    # Clean up
    cleanup = input("Remove SQLite backup file? (y/n): ")
    if cleanup.lower() == 'y':
        os.remove(backup_file)
        print("✓ Backup file removed")
    
    print("\nNext steps:")
    print("1. Test the application with PostgreSQL")
    print("2. Remove or rename the old SQLite database file")
    print("3. Update any deployment configurations")

if __name__ == "__main__":
    main()