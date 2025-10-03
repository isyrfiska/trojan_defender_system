#!/usr/bin/env python3
"""
Zero-Downtime Docker Migration Script for Trojan Defender
This script ensures seamless migration from development to Docker with comprehensive error handling.
"""

import os
import sys
import subprocess
import json
import time
import requests
import shutil
from pathlib import Path
from datetime import datetime
import signal
import psutil

class DockerMigration:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.errors = []
        self.warnings = []
        self.backup_dir = self.project_root / "migration_backup"
        self.dev_processes = {}
        
    def log_error(self, message):
        """Log an error message"""
        self.errors.append(message)
        print(f"❌ ERROR: {message}")
        
    def log_warning(self, message):
        """Log a warning message"""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")
        
    def log_success(self, message):
        """Log a success message"""
        print(f"✅ {message}")
        
    def log_info(self, message):
        """Log an info message"""
        print(f"ℹ️  {message}")
        
    def log_step(self, step, message):
        """Log a step message"""
        print(f"\n🔄 STEP {step}: {message}")
        print("=" * 60)
    
    def run_command(self, command, capture_output=True, check=True, cwd=None):
        """Run a command and return the result"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=capture_output, 
                text=True, 
                check=check,
                cwd=cwd or self.project_root
            )
            return result
        except subprocess.CalledProcessError as e:
            self.log_error(f"Command failed: {command}")
            self.log_error(f"Error: {e.stderr if e.stderr else str(e)}")
            return None
        except Exception as e:
            self.log_error(f"Unexpected error running command '{command}': {str(e)}")
            return None
    
    def create_backup(self):
        """Create backup of current configuration"""
        self.log_step(1, "Creating Configuration Backup")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup critical files
        backup_files = [
            ".env",
            "backend/.env",
            "frontend/.env",
            "docker-compose.yml",
            "backend/db.sqlite3"
        ]
        
        for file_path in backup_files:
            source = self.project_root / file_path
            if source.exists():
                dest = self.backup_dir / file_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                self.log_success(f"Backed up: {file_path}")
            else:
                self.log_warning(f"File not found for backup: {file_path}")
        
        self.log_success("Configuration backup completed")
        return True
    
    def detect_running_services(self):
        """Detect currently running development services"""
        self.log_step(2, "Detecting Running Development Services")
        
        running_services = []
        
        try:
            # Check for Django development server
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('manage.py' in str(cmd) and 'runserver' in str(cmd) for cmd in cmdline):
                        running_services.append({
                            'name': 'Django Backend',
                            'pid': proc.info['pid'],
                            'port': 8000,
                            'process': proc
                        })
                        self.log_info(f"Found Django server (PID: {proc.info['pid']})")
                    
                    # Check for npm dev server
                    elif cmdline and any('npm' in str(cmd) and 'dev' in str(cmd) for cmd in cmdline):
                        running_services.append({
                            'name': 'Frontend Dev Server',
                            'pid': proc.info['pid'],
                            'port': 3000,
                            'process': proc
                        })
                        self.log_info(f"Found Frontend server (PID: {proc.info['pid']})")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            self.log_warning(f"Could not detect all services: {e}")
        
        if not running_services:
            self.log_info("No running development services detected")
        
        self.log_success("Service detection completed")
        return running_services
    
    def validate_docker_config(self):
        """Validate Docker configuration files"""
        self.log_step(3, "Validating Docker Configuration")
        
        # Check docker-compose.yml syntax
        result = self.run_command("docker-compose config", check=False)
        if not result or result.returncode != 0:
            self.log_error("Invalid docker-compose.yml syntax")
            if result and result.stderr:
                self.log_error(f"Syntax error: {result.stderr}")
            return False
        
        self.log_success("docker-compose.yml syntax is valid")
        
        # Check required Dockerfiles
        dockerfiles = [
            "backend/Dockerfile",
            "backend/Dockerfile.worker", 
            "frontend/Dockerfile"
        ]
        
        for dockerfile in dockerfiles:
            if not (self.project_root / dockerfile).exists():
                self.log_error(f"Missing Dockerfile: {dockerfile}")
                return False
            self.log_success(f"Found Dockerfile: {dockerfile}")
        
        return len(self.errors) == 0
    
    def prepare_environment(self):
        """Prepare environment files for Docker"""
        self.log_step(4, "Preparing Environment Configuration")
        
        # Ensure root .env exists for Docker Compose
        root_env = self.project_root / ".env"
        if not root_env.exists():
            self.log_info("Creating root .env file for Docker Compose")
            with open(root_env, 'w') as f:
                f.write("""# Docker Compose Environment Variables
DB_NAME=trojan_defender
DB_USER=postgres
DB_PASSWORD=secure_password_123
DB_HOST=db
DB_PORT=5432

REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=False

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# MinIO Configuration
MINIO_ENDPOINT=object_storage:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
""")
        
        # Validate backend .env
        backend_env = self.project_root / "backend" / ".env"
        if backend_env.exists():
            self.log_success("Backend .env file exists")
        else:
            self.log_warning("Backend .env file missing - using defaults")
        
        # Validate frontend .env
        frontend_env = self.project_root / "frontend" / ".env"
        if frontend_env.exists():
            self.log_success("Frontend .env file exists")
        else:
            self.log_info("Creating frontend .env file")
            with open(frontend_env, 'w') as f:
                f.write("""VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
""")
        
        return True
    
    def build_docker_images(self):
        """Build Docker images with error handling"""
        self.log_step(5, "Building Docker Images")
        
        # Build images one by one for better error handling
        services = ["db", "redis", "scanner", "object_storage"]
        
        for service in services:
            self.log_info(f"Pulling/preparing {service} image...")
            result = self.run_command(f"docker-compose pull {service}", check=False)
            if result and result.returncode == 0:
                self.log_success(f"{service} image ready")
            else:
                self.log_warning(f"Could not pull {service} image, will build if needed")
        
        # Build custom images
        custom_services = ["api", "worker", "frontend"]
        
        for service in custom_services:
            self.log_info(f"Building {service} image...")
            result = self.run_command(f"docker-compose build {service}", check=False)
            if not result or result.returncode != 0:
                self.log_error(f"Failed to build {service} image")
                return False
            self.log_success(f"{service} image built successfully")
        
        return True
    
    def graceful_shutdown_dev_services(self):
        """Gracefully shutdown development services"""
        self.log_step(6, "Gracefully Shutting Down Development Services")
        
        for service_name, service_info in self.dev_processes.items():
            if service_info["process"]:
                try:
                    proc = psutil.Process(service_info["process"])
                    self.log_info(f"Stopping {service_name} (PID: {service_info['process']})")
                    
                    # Send SIGTERM first
                    proc.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        proc.wait(timeout=10)
                        self.log_success(f"{service_name} stopped gracefully")
                    except psutil.TimeoutExpired:
                        # Force kill if needed
                        proc.kill()
                        self.log_warning(f"{service_name} force killed")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    self.log_warning(f"Could not stop {service_name}: {str(e)}")
        
        # Wait a moment for ports to be released
        time.sleep(2)
        return True
    
    def start_docker_services(self):
        """Start Docker services with health checks"""
        self.log_step(7, "Starting Docker Services")
        
        # Start infrastructure services first
        infrastructure = ["db", "redis", "scanner", "object_storage"]
        
        for service in infrastructure:
            self.log_info(f"Starting {service}...")
            result = self.run_command(f"docker-compose up -d {service}", check=False)
            if not result or result.returncode != 0:
                self.log_error(f"Failed to start {service}")
                return False
            
            # Wait for health check
            self.log_info(f"Waiting for {service} to be healthy...")
            max_attempts = 30
            for attempt in range(max_attempts):
                result = self.run_command(f"docker-compose ps {service}", check=False)
                if result and "healthy" in result.stdout:
                    self.log_success(f"{service} is healthy")
                    break
                elif attempt == max_attempts - 1:
                    self.log_error(f"{service} failed health check")
                    return False
                time.sleep(2)
        
        # Start application services
        app_services = ["api", "worker", "frontend"]
        
        for service in app_services:
            self.log_info(f"Starting {service}...")
            result = self.run_command(f"docker-compose up -d {service}", check=False)
            if not result or result.returncode != 0:
                self.log_error(f"Failed to start {service}")
                return False
            self.log_success(f"{service} started")
        
        return True
    
    def run_migrations(self):
        """Run database migrations"""
        self.log_step(8, "Running Database Migrations")
        
        # Wait for API service to be ready
        self.log_info("Waiting for API service to be ready...")
        time.sleep(10)
        
        # Run migrations
        result = self.run_command("docker-compose exec -T api python manage.py migrate", check=False)
        if not result or result.returncode != 0:
            self.log_error("Database migrations failed")
            return False
        
        self.log_success("Database migrations completed")
        return True
    
    def validate_deployment(self):
        """Validate the Docker deployment"""
        self.log_step(9, "Validating Docker Deployment")
        
        # Check all services are running
        result = self.run_command("docker-compose ps", check=False)
        if not result or result.returncode != 0:
            self.log_error("Could not check service status")
            return False
        
        self.log_info("Service Status:")
        print(result.stdout)
        
        # Test API endpoint
        self.log_info("Testing API endpoint...")
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:8000/api/health/", timeout=5)
                if response.status_code == 200:
                    self.log_success("API endpoint is responding")
                    break
            except requests.RequestException:
                if attempt == max_attempts - 1:
                    self.log_error("API endpoint is not responding")
                    return False
                time.sleep(3)
        
        # Test frontend
        self.log_info("Testing frontend...")
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:3000", timeout=5)
                if response.status_code == 200:
                    self.log_success("Frontend is responding")
                    break
            except requests.RequestException:
                if attempt == max_attempts - 1:
                    self.log_error("Frontend is not responding")
                    return False
                time.sleep(3)
        
        return True
    
    def cleanup_on_failure(self):
        """Cleanup Docker services on failure"""
        self.log_info("Cleaning up Docker services due to failure...")
        
        # Stop all services
        self.run_command("docker-compose down", check=False)
        
        # Restore backup if needed
        if self.backup_dir.exists():
            self.log_info("Restoring configuration backup...")
            for backup_file in self.backup_dir.rglob("*"):
                if backup_file.is_file():
                    relative_path = backup_file.relative_to(self.backup_dir)
                    dest = self.project_root / relative_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file, dest)
        
        self.log_info("Cleanup completed")
    
    def generate_migration_report(self):
        """Generate migration report"""
        print("\n" + "="*60)
        print("DOCKER MIGRATION REPORT")
        print("="*60)
        
        if self.errors:
            print(f"\n❌ MIGRATION FAILED")
            print(f"   Errors encountered: {len(self.errors)}")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
            
            if self.warnings:
                print(f"\n⚠️  Warnings: {len(self.warnings)}")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"   {i}. {warning}")
            
            return False
        else:
            print(f"\n🎉 MIGRATION SUCCESSFUL!")
            print(f"   All services are running in Docker containers")
            print(f"   Frontend: http://localhost:3000")
            print(f"   Backend API: http://localhost:8000")
            print(f"   Admin Panel: http://localhost:8000/admin/")
            
            if self.warnings:
                print(f"\n⚠️  Warnings: {len(self.warnings)}")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"   {i}. {warning}")
            
            print(f"\n📋 Next Steps:")
            print(f"   1. Access the application at http://localhost:3000")
            print(f"   2. Create a superuser: docker-compose exec api python manage.py createsuperuser")
            print(f"   3. Monitor logs: docker-compose logs -f")
            print(f"   4. Stop services: docker-compose down")
            
            return True
    
    def run_migration(self):
        """Run the complete migration process"""
        print("🐳 ZERO-DOWNTIME DOCKER MIGRATION")
        print("Starting seamless migration to Docker containers...")
        
        try:
            # Execute migration steps
            if not self.create_backup():
                self.cleanup_on_failure()
                return self.generate_migration_report()
            
            running_services = self.detect_running_services()
            
            if not self.validate_docker_config():
                self.cleanup_on_failure()
                return self.generate_migration_report()
            
            if not self.prepare_environment():
                self.cleanup_on_failure()
                return self.generate_migration_report()
            
            if not self.build_docker_images():
                self.cleanup_on_failure()
                return self.generate_migration_report()
            
            # Store running services for graceful shutdown
            for service in running_services:
                self.dev_processes[service['name']] = {
                    'process': service['pid'],
                    'port': service['port']
                }
            
            if not self.graceful_shutdown_dev_services():
                self.cleanup_on_failure()
                return self.generate_migration_report()
            
            if not self.start_docker_services():
                self.cleanup_on_failure()
                return self.generate_migration_report()
            
            if not self.run_migrations():
                self.cleanup_on_failure()
                return self.generate_migration_report()
            
            if not self.validate_deployment():
                self.cleanup_on_failure()
                return self.generate_migration_report()
            
            return self.generate_migration_report()
            
        except KeyboardInterrupt:
            self.log_error("Migration interrupted by user")
            self.cleanup_on_failure()
            return False
        except Exception as e:
            self.log_error(f"Unexpected error during migration: {str(e)}")
            self.cleanup_on_failure()
            return False

def main():
    """Main migration function"""
    migration = DockerMigration()
    success = migration.run_migration()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)