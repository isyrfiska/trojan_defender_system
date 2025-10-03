#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script for Trojan Defender
This script sets up PostgreSQL database and user for the application.
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import django
from django.conf import settings
from django.core.management import execute_from_command_line

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trojan_defender.settings')
django.setup()

def check_postgresql_service():
    """Check if PostgreSQL service is running"""
    try:
        # Check if PostgreSQL is running on Windows
        result = subprocess.run(['sc', 'query', 'postgresql-x64-14'], 
                              capture_output=True, text=True, shell=True)
        if 'RUNNING' in result.stdout:
            print("✓ PostgreSQL service is running")
            return True
        else:
            print("✗ PostgreSQL service is not running")
            print("Please start PostgreSQL service manually:")
            print("  net start postgresql-x64-14")
            return False
    except Exception as e:
        print(f"Could not check PostgreSQL service: {e}")
        return False

def create_database_and_user():
    """Create database and user for the application"""
    try:
        # Database configuration from environment
        db_name = os.getenv('DB_NAME', 'trojan_defender_db')
        db_user = os.getenv('DB_USER', 'trojan_defender_user')
        db_password = os.getenv('DB_PASSWORD', 'TrojanDefender2024!SecurePass')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        
        print(f"Setting up database: {db_name}")
        print(f"Creating user: {db_user}")
        
        # Connect to PostgreSQL as superuser (postgres)
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user='postgres',
            password=input("Enter PostgreSQL superuser (postgres) password: ")
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create user if not exists
        cursor.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{db_user}') THEN
                    CREATE USER {db_user} WITH PASSWORD '{db_password}';
                END IF;
            END
            $$;
        """)
        print(f"✓ User '{db_user}' created/verified")
        
        # Create database if not exists
        cursor.execute(f"""
            SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'
        """)
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {db_name} OWNER {db_user}")
            print(f"✓ Database '{db_name}' created")
        else:
            print(f"✓ Database '{db_name}' already exists")
        
        # Grant privileges
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user}")
        cursor.execute(f"ALTER USER {db_user} CREATEDB")
        print(f"✓ Privileges granted to '{db_user}'")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Database setup failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_connection():
    """Test connection to the application database"""
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✓ Database connection successful")
        print(f"  PostgreSQL version: {version}")
        cursor.close()
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def run_migrations():
    """Run Django migrations"""
    try:
        print("Running Django migrations...")
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        print("✓ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

def create_superuser():
    """Create Django superuser"""
    try:
        print("\nCreating Django superuser...")
        execute_from_command_line(['manage.py', 'createsuperuser'])
        return True
    except Exception as e:
        print(f"✗ Superuser creation failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("PostgreSQL Database Setup for Trojan Defender")
    print("=" * 60)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Step 1: Check PostgreSQL service
    if not check_postgresql_service():
        print("\nPlease ensure PostgreSQL is installed and running.")
        sys.exit(1)
    
    # Step 2: Create database and user
    if not create_database_and_user():
        print("\nDatabase setup failed. Please check your PostgreSQL installation.")
        sys.exit(1)
    
    # Step 3: Test connection
    if not test_connection():
        print("\nConnection test failed. Please check your configuration.")
        sys.exit(1)
    
    # Step 4: Run migrations
    if not run_migrations():
        print("\nMigration failed. Please check for errors.")
        sys.exit(1)
    
    # Step 5: Create superuser (optional)
    create_superuser_choice = input("\nWould you like to create a Django superuser? (y/n): ")
    if create_superuser_choice.lower() == 'y':
        create_superuser()
    
    print("\n" + "=" * 60)
    print("✓ PostgreSQL setup completed successfully!")
    print("✓ Database is ready for use")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Start the Django development server: python manage.py runserver")
    print("2. Access the admin panel at: http://localhost:8000/admin/")
    print("3. Test the application functionality")

if __name__ == "__main__":
    main()