#!/usr/bin/env python
import os
import sys
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trojan_defender.settings')
django.setup()

def mark_migration_applied():
    """Mark the users migration as applied."""
    with connection.cursor() as cursor:
        # Check if migration is already marked as applied
        cursor.execute("""
            SELECT id FROM django_migrations 
            WHERE app = 'users' AND name = '0001_initial';
        """)
        
        if cursor.fetchone():
            print("Migration users.0001_initial is already marked as applied.")
            return
        
        # Mark the migration as applied
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('users', '0001_initial', datetime('now'));
        """)
        
        print("Migration users.0001_initial marked as applied.")

if __name__ == '__main__':
    mark_migration_applied()