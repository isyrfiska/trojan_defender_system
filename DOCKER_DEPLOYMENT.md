# Docker Deployment Guide

This guide explains how to deploy the Trojan Defender application using Docker and Docker Compose.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0 or higher
- At least 4GB of available RAM
- At least 10GB of available disk space

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd trojan_defender
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
nano .env  # or use your preferred editor
```

**Important**: Update these values in your `.env` file:
- `SECRET_KEY`: Generate a new Django secret key
- `DB_PASSWORD`: Set a secure database password
- `JWT_SECRET_KEY`: Generate a new JWT secret key
- `MINIO_ROOT_PASSWORD`: Set a secure MinIO password
- Email settings for notifications

### 3. Deploy

#### Development Mode
```bash
# Linux/Mac
./deploy.sh start dev

# Windows
deploy.bat start dev
```

#### Production Mode
```bash
# Linux/Mac
./deploy.sh start prod

# Windows
deploy.bat start prod
```

### 4. Initial Setup

After deployment, run these commands:

```bash
# Run database migrations
./deploy.sh migrate

# Create superuser account
./deploy.sh superuser

# Collect static files (production only)
./deploy.sh collectstatic
```

## Service Architecture

The application consists of the following services:

### Core Services
- **frontend**: React.js application (Nginx + Vite)
- **api**: Django REST API backend
- **worker**: Celery worker for background tasks
- **beat**: Celery beat scheduler

### Infrastructure Services
- **db**: PostgreSQL database
- **redis**: Redis for caching and message broker
- **scanner**: ClamAV antivirus daemon
- **object_storage**: MinIO for file storage
- **traefik**: Reverse proxy and SSL termination (production only)

## Configuration Files

### Docker Compose Files
- `docker-compose.yml`: Base configuration
- `docker-compose.override.yml`: Development overrides (auto-loaded)
- `docker-compose.prod.yml`: Production configuration

### Dockerfiles
- `backend/Dockerfile`: Django API service
- `backend/Dockerfile.worker`: Celery worker service
- `frontend/Dockerfile`: React frontend service
- `frontend/nginx.conf`: Nginx configuration

## Deployment Scripts

### Linux/Mac: `deploy.sh`
```bash
./deploy.sh [COMMAND] [OPTIONS]
```

### Windows: `deploy.bat`
```cmd
deploy.bat [COMMAND] [OPTIONS]
```

### Available Commands
- `start [dev|prod]`: Start services
- `stop`: Stop all services
- `restart [dev|prod]`: Restart services
- `logs [service]`: Show logs
- `migrate`: Run database migrations
- `superuser`: Create Django superuser
- `collectstatic`: Collect static files
- `backup`: Backup database
- `restore <file>`: Restore database
- `status`: Show service status

## Development vs Production

### Development Mode
- Hot reloading enabled
- Debug mode on
- Source code mounted as volumes
- Services accessible on localhost
- SQLite database (optional)

### Production Mode
- Optimized builds
- Debug mode off
- SSL/TLS termination with Traefik
- Health checks enabled
- Resource limits applied
- PostgreSQL database required

## Port Mapping

### Development
- Frontend: http://localhost:3000
- API: http://localhost:8000
- MinIO Console: http://localhost:9001
- ClamAV: localhost:3310

### Production
- Frontend: https://your-domain.com
- API: https://api.your-domain.com
- Traefik Dashboard: https://traefik.your-domain.com
- MinIO Console: https://minio.your-domain.com

## Data Persistence

The following volumes are created for data persistence:
- `postgres_data`: Database files
- `redis_data`: Redis data
- `clamav_data`: ClamAV virus definitions
- `minio_data`: Object storage files
- `traefik_certs`: SSL certificates (production)

## Backup and Restore

### Database Backup
```bash
./deploy.sh backup
```

### Database Restore
```bash
./deploy.sh restore /path/to/backup.sql
```

### File Storage Backup
```bash
# Backup MinIO data
docker run --rm -v minio_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/minio_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

## Monitoring and Logs

### View Logs
```bash
# All services
./deploy.sh logs

# Specific service
./deploy.sh logs api
./deploy.sh logs worker
./deploy.sh logs frontend
```

### Service Status
```bash
./deploy.sh status
```

### Resource Usage
```bash
docker stats
```

## Scaling

### Scale Workers
```bash
docker-compose up -d --scale worker=3
```

### Scale API Instances (Production)
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale api=2
```

## Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use strong passwords for all services
- Rotate secrets regularly

### Network Security
- All services communicate through internal Docker network
- Only necessary ports are exposed
- Traefik handles SSL termination in production

### File Permissions
```bash
# Make deployment scripts executable
chmod +x deploy.sh
```

## Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check logs
./deploy.sh logs

# Check service status
./deploy.sh status

# Restart services
./deploy.sh restart
```

#### Database Connection Issues
```bash
# Check database logs
./deploy.sh logs db

# Verify environment variables
cat .env | grep SQL_
```

#### ClamAV Not Working
```bash
# Check ClamAV logs
./deploy.sh logs scanner

# Update virus definitions
docker-compose exec scanner freshclam
```

#### Frontend Build Issues
```bash
# Rebuild frontend
docker-compose build frontend

# Check frontend logs
./deploy.sh logs frontend
```

### Performance Tuning

#### Database Optimization
```sql
-- Connect to database
docker-compose exec db psql -U postgres -d trojan_defender

-- Check database size
SELECT pg_size_pretty(pg_database_size('trojan_defender'));

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM scanner_scanresult LIMIT 10;
```

#### Redis Optimization
```bash
# Check Redis memory usage
docker-compose exec redis redis-cli info memory

# Monitor Redis commands
docker-compose exec redis redis-cli monitor
```

## Maintenance

### Regular Tasks
1. Update virus definitions (automatic with ClamAV)
2. Backup database weekly
3. Monitor disk usage
4. Review logs for errors
5. Update Docker images monthly

### Updates
```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
./deploy.sh restart prod
```

### Cleanup
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune
```

## Support

For issues and questions:
1. Check the logs first
2. Review this documentation
3. Check Docker and Docker Compose documentation
4. Open an issue in the project repository

## License

This deployment configuration is part of the Trojan Defender project and follows the same license terms.