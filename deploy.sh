#!/bin/bash

# Trojan Defender Deployment Script
# This script helps deploy the Trojan Defender application using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed."
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your actual configuration values."
            print_warning "Pay special attention to:"
            echo "  - SECRET_KEY (generate a new one)"
            echo "  - DB_PASSWORD (set a secure password)"
            echo "  - JWT_SECRET_KEY (generate a new one)"
            echo "  - EMAIL_* settings (configure your email provider)"
            echo "  - MINIO_ROOT_PASSWORD (set a secure password)"
            read -p "Press Enter after updating .env file..."
        else
            print_error ".env.example file not found. Cannot create .env file."
            exit 1
        fi
    else
        print_success ".env file found."
    fi
}

# Function to build and start services
start_services() {
    local mode=$1
    
    print_status "Building Docker images..."
    
    if [ "$mode" = "production" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
        print_status "Starting services in production mode..."
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    else
        docker-compose build
        print_status "Starting services in development mode..."
        docker-compose up -d
    fi
    
    print_success "Services started successfully!"
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose down
    print_success "Services stopped."
}

# Function to show logs
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$service"
    fi
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    docker-compose exec api python manage.py migrate
    print_success "Migrations completed."
}

# Function to create superuser
create_superuser() {
    print_status "Creating Django superuser..."
    docker-compose exec api python manage.py createsuperuser
}

# Function to collect static files
collect_static() {
    print_status "Collecting static files..."
    docker-compose exec api python manage.py collectstatic --noinput
    print_success "Static files collected."
}

# Function to backup database
backup_database() {
    local backup_dir="./backups"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="${backup_dir}/db_backup_${timestamp}.sql"
    
    mkdir -p "$backup_dir"
    
    print_status "Creating database backup..."
    docker-compose exec db pg_dump -U postgres trojan_defender > "$backup_file"
    print_success "Database backup created: $backup_file"
}

# Function to restore database
restore_database() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        print_error "Please specify backup file path."
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_status "Restoring database from: $backup_file"
    docker-compose exec -T db psql -U postgres -d trojan_defender < "$backup_file"
    print_success "Database restored successfully."
}

# Function to show help
show_help() {
    echo "Trojan Defender Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [dev|prod]     Start services (default: dev)"
    echo "  stop                 Stop all services"
    echo "  restart [dev|prod]   Restart services"
    echo "  logs [service]       Show logs (all services or specific service)"
    echo "  migrate              Run database migrations"
    echo "  superuser            Create Django superuser"
    echo "  collectstatic        Collect static files"
    echo "  backup               Backup database"
    echo "  restore <file>       Restore database from backup"
    echo "  status               Show service status"
    echo "  help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start dev         Start in development mode"
    echo "  $0 start prod        Start in production mode"
    echo "  $0 logs api          Show API service logs"
    echo "  $0 restore backup.sql Restore from backup.sql"
}

# Main script logic
case "$1" in
    "start")
        check_docker
        check_env_file
        mode=${2:-"dev"}
        start_services "$mode"
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        mode=${2:-"dev"}
        start_services "$mode"
        ;;
    "logs")
        show_logs "$2"
        ;;
    "migrate")
        run_migrations
        ;;
    "superuser")
        create_superuser
        ;;
    "collectstatic")
        collect_static
        ;;
    "backup")
        backup_database
        ;;
    "restore")
        restore_database "$2"
        ;;
    "status")
        docker-compose ps
        ;;
    "help"|"")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac