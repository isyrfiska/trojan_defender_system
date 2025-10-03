@echo off
setlocal enabledelayedexpansion

REM Trojan Defender Deployment Script for Windows
REM This script helps deploy the Trojan Defender application using Docker Compose

set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Function to print colored output
:print_status
echo %BLUE%[INFO]%NC% %~1
goto :eof

:print_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:print_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:print_error
echo %RED%[ERROR]%NC% %~1
goto :eof

REM Function to check if Docker is installed
:check_docker
docker --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker is not installed. Please install Docker Desktop first."
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit /b 1
)

call :print_success "Docker and Docker Compose are installed."
goto :eof

REM Function to check if .env file exists
:check_env_file
if not exist ".env" (
    call :print_warning ".env file not found. Creating from .env.example..."
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        call :print_warning "Please edit .env file with your actual configuration values."
        call :print_warning "Pay special attention to:"
        echo   - SECRET_KEY (generate a new one)
        echo   - DB_PASSWORD (set a secure password)
        echo   - JWT_SECRET_KEY (generate a new one)
        echo   - EMAIL_* settings (configure your email provider)
        echo   - MINIO_ROOT_PASSWORD (set a secure password)
        pause
    ) else (
        call :print_error ".env.example file not found. Cannot create .env file."
        exit /b 1
    )
) else (
    call :print_success ".env file found."
)
goto :eof

REM Function to build and start services
:start_services
set "mode=%~1"

call :print_status "Building Docker images..."

if "%mode%"=="production" (
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
    call :print_status "Starting services in production mode..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
) else (
    docker-compose build
    call :print_status "Starting services in development mode..."
    docker-compose up -d
)

call :print_success "Services started successfully!"
goto :eof

REM Function to stop services
:stop_services
call :print_status "Stopping services..."
docker-compose down
call :print_success "Services stopped."
goto :eof

REM Function to show logs
:show_logs
set "service=%~1"
if "%service%"=="" (
    docker-compose logs -f
) else (
    docker-compose logs -f "%service%"
)
goto :eof

REM Function to run database migrations
:run_migrations
call :print_status "Running database migrations..."
docker-compose exec api python manage.py migrate
call :print_success "Migrations completed."
goto :eof

REM Function to create superuser
:create_superuser
call :print_status "Creating Django superuser..."
docker-compose exec api python manage.py createsuperuser
goto :eof

REM Function to collect static files
:collect_static
call :print_status "Collecting static files..."
docker-compose exec api python manage.py collectstatic --noinput
call :print_success "Static files collected."
goto :eof

REM Function to backup database
:backup_database
set "backup_dir=.\backups"
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "timestamp=%dt:~0,4%%dt:~4,2%%dt:~6,2%_%dt:~8,2%%dt:~10,2%%dt:~12,2%"
set "backup_file=%backup_dir%\db_backup_%timestamp%.sql"

if not exist "%backup_dir%" mkdir "%backup_dir%"

call :print_status "Creating database backup..."
docker-compose exec db pg_dump -U postgres trojan_defender > "%backup_file%"
call :print_success "Database backup created: %backup_file%"
goto :eof

REM Function to restore database
:restore_database
set "backup_file=%~1"

if "%backup_file%"=="" (
    call :print_error "Please specify backup file path."
    exit /b 1
)

if not exist "%backup_file%" (
    call :print_error "Backup file not found: %backup_file%"
    exit /b 1
)

call :print_status "Restoring database from: %backup_file%"
docker-compose exec -T db psql -U postgres -d trojan_defender < "%backup_file%"
call :print_success "Database restored successfully."
goto :eof

REM Function to show help
:show_help
echo Trojan Defender Deployment Script for Windows
echo.
echo Usage: %~nx0 [COMMAND] [OPTIONS]
echo.
echo Commands:
echo   start [dev^|prod]     Start services (default: dev)
echo   stop                 Stop all services
echo   restart [dev^|prod]   Restart services
echo   logs [service]       Show logs (all services or specific service)
echo   migrate              Run database migrations
echo   superuser            Create Django superuser
echo   collectstatic        Collect static files
echo   backup               Backup database
echo   restore ^<file^>       Restore database from backup
echo   status               Show service status
echo   help                 Show this help message
echo.
echo Examples:
echo   %~nx0 start dev         Start in development mode
echo   %~nx0 start prod        Start in production mode
echo   %~nx0 logs api          Show API service logs
echo   %~nx0 restore backup.sql Restore from backup.sql
goto :eof

REM Main script logic
if "%1"=="start" (
    call :check_docker
    call :check_env_file
    set "mode=%2"
    if "%mode%"=="" set "mode=dev"
    call :start_services "%mode%"
) else if "%1"=="stop" (
    call :stop_services
) else if "%1"=="restart" (
    call :stop_services
    set "mode=%2"
    if "%mode%"=="" set "mode=dev"
    call :start_services "%mode%"
) else if "%1"=="logs" (
    call :show_logs "%2"
) else if "%1"=="migrate" (
    call :run_migrations
) else if "%1"=="superuser" (
    call :create_superuser
) else if "%1"=="collectstatic" (
    call :collect_static
) else if "%1"=="backup" (
    call :backup_database
) else if "%1"=="restore" (
    call :restore_database "%2"
) else if "%1"=="status" (
    docker-compose ps
) else if "%1"=="help" (
    call :show_help
) else if "%1"=="" (
    call :show_help
) else (
    call :print_error "Unknown command: %1"
    call :show_help
    exit /b 1
)