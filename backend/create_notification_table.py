#!/usr/bin/env python
import os
import sys
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trojan_defender.settings')
django.setup()

def create_notification_table():
    """Create the notification table manually."""
    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users_notification';
        """)
        
        if cursor.fetchone():
            print("Notification table already exists.")
            return
        
        # Create the notification table
        cursor.execute("""
            CREATE TABLE "users_notification" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "title" varchar(255) NOT NULL,
                "message" text NOT NULL,
                "notification_type" varchar(50) NOT NULL,
                "priority" varchar(20) NOT NULL,
                "is_read" bool NOT NULL,
                "timestamp" datetime NOT NULL,
                "read_at" datetime NULL,
                "scan_result_id" integer NULL,
                "threat_id" integer NULL,
                "user_id" bigint NOT NULL REFERENCES "users_user" ("id") DEFERRABLE INITIALLY DEFERRED
            );
        """)
        
        # Create index on user_id
        cursor.execute("""
            CREATE INDEX "users_notification_user_id_idx" 
            ON "users_notification" ("user_id");
        """)
        
        # Create index on timestamp for ordering
        cursor.execute("""
            CREATE INDEX "users_notification_timestamp_idx" 
            ON "users_notification" ("timestamp");
        """)
        
        print("Notification table created successfully.")

if __name__ == '__main__':
    create_notification_table()