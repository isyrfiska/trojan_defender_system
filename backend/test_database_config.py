#!/usr/bin/env python3
"""
Database Configuration Test Script for Trojan Defender
This script tests the PostgreSQL database configuration and connection.
"""

import os
import sys
import django
from django.db import connection, connections
from django.core.management import execute_from_command_line
from django.conf import settings

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trojan_defender.settings')

def load_environment():
    """Load environment variables"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Environment variables loaded")
        return True
    except ImportError:
        print("✗ python-dotenv not installed")
        return False

def check_database_config():
    """Check database configuration"""
    django.setup()
    
    print("\nDatabase Configuration:")
    print("-" * 40)
    
    db_config = settings.DATABASES['default']
    
    for key, value in db_config.items():
        if key == 'PASSWORD':
            print(f"  {key}: {'*' * len(str(value))}")
        else:
            print(f"  {key}: {value}")
    
    return db_config

def test_database_connection():
    """Test database connection"""
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        
        print(f"\n✓ Database connection successful")
        print(f"  PostgreSQL version: {version}")
        return True
        
    except Exception as e:
        print(f"\n✗ Database connection failed: {e}")
        return False

def test_connection_pooling():
    """Test connection pooling settings"""
    try:
        db_config = settings.DATABASES['default']
        conn_max_age = db_config.get('CONN_MAX_AGE', 0)
        conn_health_checks = db_config.get('CONN_HEALTH_CHECKS', False)
        
        print(f"\nConnection Pooling Settings:")
        print(f"  CONN_MAX_AGE: {conn_max_age} seconds")
        print(f"  CONN_HEALTH_CHECKS: {conn_health_checks}")
        
        if conn_max_age > 0:
            print("✓ Connection pooling is enabled")
        else:
            print("⚠ Connection pooling is disabled")
        
        return True
        
    except Exception as e:
        print(f"✗ Connection pooling test failed: {e}")
        return False

def test_database_operations():
    """Test basic database operations"""
    try:
        cursor = connection.cursor()
        
        # Test table creation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Test insert
        cursor.execute("INSERT INTO test_table (name) VALUES (%s)", ['test_record'])
        
        # Test select
        cursor.execute("SELECT COUNT(*) FROM test_table")
        count = cursor.fetchone()[0]
        
        # Test delete
        cursor.execute("DELETE FROM test_table WHERE name = %s", ['test_record'])
        
        # Drop test table
        cursor.execute("DROP TABLE test_table")
        
        cursor.close()
        
        print("✓ Basic database operations successful")
        return True
        
    except Exception as e:
        print(f"✗ Database operations test failed: {e}")
        return False

def check_required_packages():
    """Check if required packages are installed"""
    required_packages = [
        'psycopg2',
        'django_db_connection_pool',
        'django',
    ]
    
    print("\nRequired Packages:")
    print("-" * 40)
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")
            all_installed = False
    
    return all_installed

def check_django_apps():
    """Check Django apps configuration"""
    try:
        django.setup()
        
        print("\nDjango Apps:")
        print("-" * 40)
        
        for app in settings.INSTALLED_APPS:
            print(f"  - {app}")
        
        return True
        
    except Exception as e:
        print(f"✗ Django apps check failed: {e}")
        return False

def run_migrations_check():
    """Check if migrations need to be run"""
    try:
        from django.core.management.commands.migrate import Command
        from django.db.migrations.executor import MigrationExecutor
        
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            print(f"\n⚠ {len(plan)} pending migrations found")
            print("Run 'python manage.py migrate' to apply them")
            return False
        else:
            print("\n✓ All migrations are up to date")
            return True
            
    except Exception as e:
        print(f"\n✗ Migration check failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Database Configuration Test for Trojan Defender")
    print("=" * 60)
    
    success_count = 0
    total_tests = 7
    
    # Test 1: Load environment
    if load_environment():
        success_count += 1
    
    # Test 2: Check required packages
    if check_required_packages():
        success_count += 1
    
    # Test 3: Check database configuration
    try:
        check_database_config()
        success_count += 1
    except Exception as e:
        print(f"✗ Database config check failed: {e}")
    
    # Test 4: Test database connection
    if test_database_connection():
        success_count += 1
    
    # Test 5: Test connection pooling
    if test_connection_pooling():
        success_count += 1
    
    # Test 6: Test database operations
    if test_database_operations():
        success_count += 1
    
    # Test 7: Check migrations
    if run_migrations_check():
        success_count += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("✓ All database tests passed!")
        print("✓ PostgreSQL configuration is working correctly")
    else:
        print(f"✗ {total_tests - success_count} tests failed")
        print("Please check the configuration and try again")
    
    print("=" * 60)

if __name__ == "__main__":
    main()