# Deployment Guide

This guide covers deploying Trojan Defender in production environments, including Docker, cloud platforms, and traditional server deployments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Traditional Server Deployment](#traditional-server-deployment)
- [Load Balancing](#load-balancing)
- [Database Configuration](#database-configuration)
- [Security Hardening](#security-hardening)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Recovery](#backup-and-recovery)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores, 2.4 GHz
- **RAM**: 4 GB
- **Storage**: 20 GB SSD
- **Network**: 100 Mbps
- **OS**: Ubuntu 20.04+, CentOS 8+, or Windows Server 2019+

#### Recommended Requirements
- **CPU**: 4+ cores, 3.0 GHz
- **RAM**: 8+ GB
- **Storage**: 100+ GB SSD
- **Network**: 1 Gbps
- **OS**: Ubuntu 22.04 LTS

#### High-Traffic Requirements
- **CPU**: 8+ cores, 3.5 GHz
- **RAM**: 16+ GB
- **Storage**: 500+ GB NVMe SSD
- **Network**: 10 Gbps
- **Load Balancer**: Required
- **Database**: Separate server recommended

### Software Dependencies

#### Required Software
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.9+ (for non-Docker deployments)
- **Node.js**: 18+ (for non-Docker deployments)
- **PostgreSQL**: 13+ or MySQL 8.0+
- **Redis**: 6.0+

#### Optional Software
- **Nginx**: For reverse proxy
- **Let's Encrypt**: For SSL certificates
- **Prometheus**: For monitoring
- **Grafana**: For dashboards
- **ELK Stack**: For logging

## Docker Deployment

### Production Docker Compose

Create a production-ready `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: trojan_defender
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - backend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - backend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/trojan_defender
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}
    volumes:
      - media_files:/app/media
      - static_files:/app/static
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    networks:
      - backend
      - frontend
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - REACT_APP_API_URL=${API_URL}
      - REACT_APP_WS_URL=${WS_URL}
    networks:
      - frontend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/sites-enabled:/etc/nginx/sites-enabled
      - ./ssl:/etc/nginx/ssl
      - static_files:/var/www/static
      - media_files:/var/www/media
    depends_on:
      - backend
      - frontend
    networks:
      - frontend
    restart: unless-stopped

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A trojan_defender worker -l info
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/trojan_defender
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    volumes:
      - media_files:/app/media
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    networks:
      - backend
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A trojan_defender beat -l info
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/trojan_defender
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    volumes:
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    networks:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  media_files:
  static_files:

networks:
  frontend:
  backend:
```

### Production Environment Variables

Create `.env.prod`:

```bash
# Database
DB_USER=trojan_defender_user
DB_PASSWORD=your_secure_db_password

# Redis
REDIS_PASSWORD=your_secure_redis_password

# Django
SECRET_KEY=your_very_long_secret_key_here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# URLs
API_URL=https://yourdomain.com/api
WS_URL=wss://yourdomain.com/ws

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Deployment Steps

1. **Prepare Server**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/trojan-defender.git
   cd trojan-defender
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env.prod
   # Edit .env.prod with your values
   nano .env.prod
   ```

4. **Build and Deploy**
   ```bash
   # Build images
   docker-compose -f docker-compose.prod.yml build
   
   # Start services
   docker-compose -f docker-compose.prod.yml up -d
   
   # Run migrations
   docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
   
   # Create superuser
   docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
   
   # Collect static files
   docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
   ```

5. **Verify Deployment**
   ```bash
   # Check service status
   docker-compose -f docker-compose.prod.yml ps
   
   # Check logs
   docker-compose -f docker-compose.prod.yml logs
   
   # Test endpoints
   curl -I http://localhost/api/health/
   ```

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS

1. **Create ECS Cluster**
   ```bash
   aws ecs create-cluster --cluster-name trojan-defender-cluster
   ```

2. **Create Task Definition**
   ```json
   {
     "family": "trojan-defender",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "1024",
     "memory": "2048",
     "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "backend",
         "image": "your-account.dkr.ecr.region.amazonaws.com/trojan-defender-backend:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "DATABASE_URL",
             "value": "postgresql://user:pass@rds-endpoint:5432/db"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/trojan-defender",
             "awslogs-region": "us-west-2",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

3. **Create Service**
   ```bash
   aws ecs create-service \
     --cluster trojan-defender-cluster \
     --service-name trojan-defender-service \
     --task-definition trojan-defender \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
   ```

#### Using AWS Elastic Beanstalk

1. **Install EB CLI**
   ```bash
   pip install awsebcli
   ```

2. **Initialize Application**
   ```bash
   eb init trojan-defender
   eb create production
   ```

3. **Configure Environment**
   ```bash
   eb setenv SECRET_KEY=your_secret_key DATABASE_URL=your_db_url
   ```

4. **Deploy**
   ```bash
   eb deploy
   ```

### Google Cloud Platform

#### Using Google Cloud Run

1. **Build and Push Images**
   ```bash
   # Configure Docker for GCR
   gcloud auth configure-docker
   
   # Build and push backend
   docker build -t gcr.io/your-project/trojan-defender-backend ./backend
   docker push gcr.io/your-project/trojan-defender-backend
   
   # Build and push frontend
   docker build -t gcr.io/your-project/trojan-defender-frontend ./frontend
   docker push gcr.io/your-project/trojan-defender-frontend
   ```

2. **Deploy to Cloud Run**
   ```bash
   # Deploy backend
   gcloud run deploy trojan-defender-backend \
     --image gcr.io/your-project/trojan-defender-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   
   # Deploy frontend
   gcloud run deploy trojan-defender-frontend \
     --image gcr.io/your-project/trojan-defender-frontend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

#### Using Google Kubernetes Engine

1. **Create Cluster**
   ```bash
   gcloud container clusters create trojan-defender-cluster \
     --num-nodes 3 \
     --zone us-central1-a
   ```

2. **Deploy Application**
   ```bash
   kubectl apply -f k8s/
   ```

### Microsoft Azure

#### Using Azure Container Instances

1. **Create Resource Group**
   ```bash
   az group create --name trojan-defender-rg --location eastus
   ```

2. **Deploy Container Group**
   ```bash
   az container create \
     --resource-group trojan-defender-rg \
     --name trojan-defender \
     --image your-registry/trojan-defender:latest \
     --dns-name-label trojan-defender \
     --ports 80
   ```

## Traditional Server Deployment

### Ubuntu/Debian Deployment

1. **System Preparation**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install dependencies
   sudo apt install -y python3 python3-pip python3-venv nodejs npm postgresql postgresql-contrib redis-server nginx
   
   # Install Python dependencies
   sudo apt install -y python3-dev libpq-dev
   ```

2. **Database Setup**
   ```bash
   # Create database user
   sudo -u postgres createuser --interactive trojan_defender
   
   # Create database
   sudo -u postgres createdb trojan_defender
   
   # Set password
   sudo -u postgres psql -c "ALTER USER trojan_defender PASSWORD 'your_password';"
   ```

3. **Application Setup**
   ```bash
   # Create application user
   sudo useradd -m -s /bin/bash trojan_defender
   sudo su - trojan_defender
   
   # Clone repository
   git clone https://github.com/yourusername/trojan-defender.git
   cd trojan-defender
   
   # Setup backend
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Setup frontend
   cd ../frontend
   npm install
   npm run build
   ```

4. **Configuration**
   ```bash
   # Backend configuration
   cd backend
   cp .env.example .env
   # Edit .env with production values
   
   # Run migrations
   python manage.py migrate
   python manage.py collectstatic
   python manage.py createsuperuser
   ```

5. **Service Configuration**
   
   Create systemd service files:
   
   `/etc/systemd/system/trojan-defender.service`:
   ```ini
   [Unit]
   Description=Trojan Defender Backend
   After=network.target postgresql.service redis.service
   
   [Service]
   Type=notify
   User=trojan_defender
   Group=trojan_defender
   WorkingDirectory=/home/trojan_defender/trojan-defender/backend
   Environment=PATH=/home/trojan_defender/trojan-defender/backend/venv/bin
   ExecStart=/home/trojan_defender/trojan-defender/backend/venv/bin/gunicorn --workers 3 --bind unix:/run/trojan-defender.sock trojan_defender.wsgi:application
   ExecReload=/bin/kill -s HUP $MAINPID
   Restart=on-failure
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   `/etc/systemd/system/trojan-defender-celery.service`:
   ```ini
   [Unit]
   Description=Trojan Defender Celery Worker
   After=network.target redis.service
   
   [Service]
   Type=forking
   User=trojan_defender
   Group=trojan_defender
   WorkingDirectory=/home/trojan_defender/trojan-defender/backend
   Environment=PATH=/home/trojan_defender/trojan-defender/backend/venv/bin
   ExecStart=/home/trojan_defender/trojan-defender/backend/venv/bin/celery -A trojan_defender worker --detach
   ExecStop=/home/trojan_defender/trojan-defender/backend/venv/bin/celery -A trojan_defender control shutdown
   Restart=on-failure
   
   [Install]
   WantedBy=multi-user.target
   ```

6. **Nginx Configuration**
   
   `/etc/nginx/sites-available/trojan-defender`:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com www.yourdomain.com;
       
       # Redirect HTTP to HTTPS
       return 301 https://$server_name$request_uri;
   }
   
   server {
       listen 443 ssl http2;
       server_name yourdomain.com www.yourdomain.com;
       
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
       
       # Security headers
       add_header X-Frame-Options DENY;
       add_header X-Content-Type-Options nosniff;
       add_header X-XSS-Protection "1; mode=block";
       add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
       
       # Frontend
       location / {
           root /home/trojan_defender/trojan-defender/frontend/build;
           try_files $uri $uri/ /index.html;
       }
       
       # API
       location /api/ {
           proxy_pass http://unix:/run/trojan-defender.sock;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       # WebSocket
       location /ws/ {
           proxy_pass http://unix:/run/trojan-defender.sock;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       # Static files
       location /static/ {
           alias /home/trojan_defender/trojan-defender/backend/static/;
       }
       
       # Media files
       location /media/ {
           alias /home/trojan_defender/trojan-defender/backend/media/;
       }
   }
   ```

7. **Enable Services**
   ```bash
   # Enable and start services
   sudo systemctl enable trojan-defender
   sudo systemctl enable trojan-defender-celery
   sudo systemctl start trojan-defender
   sudo systemctl start trojan-defender-celery
   
   # Enable nginx site
   sudo ln -s /etc/nginx/sites-available/trojan-defender /etc/nginx/sites-enabled/
   sudo systemctl reload nginx
   ```

## Load Balancing

### Nginx Load Balancer

```nginx
upstream backend {
    least_conn;
    server backend1.example.com:8000 weight=3;
    server backend2.example.com:8000 weight=2;
    server backend3.example.com:8000 weight=1 backup;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Health check
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
}
```

### HAProxy Configuration

```
global
    daemon
    maxconn 4096

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    option httpchk GET /api/health/

frontend web_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/yourdomain.com.pem
    redirect scheme https if !{ ssl_fc }
    default_backend web_servers

backend web_servers
    balance roundrobin
    server web1 10.0.1.10:8000 check
    server web2 10.0.1.11:8000 check
    server web3 10.0.1.12:8000 check backup
```

## Database Configuration

### PostgreSQL Optimization

```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 200
random_page_cost = 1.1
effective_io_concurrency = 200

-- Enable logging
log_statement = 'all'
log_duration = on
log_min_duration_statement = 1000
```

### Database Replication

1. **Master Configuration**
   ```sql
   -- postgresql.conf
   wal_level = replica
   max_wal_senders = 3
   wal_keep_segments = 64
   
   -- pg_hba.conf
   host replication replicator 10.0.1.0/24 md5
   ```

2. **Slave Configuration**
   ```bash
   # Create base backup
   pg_basebackup -h master-ip -D /var/lib/postgresql/data -U replicator -v -P -W
   
   # recovery.conf
   standby_mode = 'on'
   primary_conninfo = 'host=master-ip port=5432 user=replicator'
   ```

### Redis Configuration

```conf
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
requirepass your_secure_password
bind 127.0.0.1
port 6379
```

## Security Hardening

### SSL/TLS Configuration

1. **Let's Encrypt Setup**
   ```bash
   # Install Certbot
   sudo apt install certbot python3-certbot-nginx
   
   # Obtain certificate
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   
   # Auto-renewal
   sudo crontab -e
   # Add: 0 12 * * * /usr/bin/certbot renew --quiet
   ```

2. **SSL Configuration**
   ```nginx
   ssl_protocols TLSv1.2 TLSv1.3;
   ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
   ssl_prefer_server_ciphers off;
   ssl_session_cache shared:SSL:10m;
   ssl_session_timeout 10m;
   ssl_stapling on;
   ssl_stapling_verify on;
   ```

### Firewall Configuration

```bash
# UFW setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Fail2ban setup
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Application Security

1. **Django Settings**
   ```python
   # settings.py
   SECURE_SSL_REDIRECT = True
   SECURE_HSTS_SECONDS = 31536000
   SECURE_HSTS_INCLUDE_SUBDOMAINS = True
   SECURE_HSTS_PRELOAD = True
   SECURE_CONTENT_TYPE_NOSNIFF = True
   SECURE_BROWSER_XSS_FILTER = True
   X_FRAME_OPTIONS = 'DENY'
   CSRF_COOKIE_SECURE = True
   SESSION_COOKIE_SECURE = True
   SESSION_COOKIE_HTTPONLY = True
   ```

2. **Environment Variables**
   ```bash
   # Use strong secrets
   SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
   
   # Database credentials
   DB_PASSWORD=$(openssl rand -base64 32)
   REDIS_PASSWORD=$(openssl rand -base64 32)
   ```

## Monitoring and Logging

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'trojan-defender'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']
```

### Grafana Dashboards

1. **Application Metrics**
   - Request rate and response time
   - Error rates and status codes
   - Database query performance
   - Celery task metrics

2. **System Metrics**
   - CPU and memory usage
   - Disk I/O and network traffic
   - Database connections
   - Redis memory usage

### Centralized Logging

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

## Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/database"
DB_NAME="trojan_defender"
DB_USER="trojan_defender"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h localhost -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Remove backups older than 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
# aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://your-backup-bucket/database/
```

### Application Backup

```bash
#!/bin/bash
# backup-app.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/application"
APP_DIR="/home/trojan_defender/trojan-defender"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C $APP_DIR/backend media/

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz -C $APP_DIR .env* docker-compose*.yml nginx/

# Remove old backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### Automated Backup

```bash
# Add to crontab
0 2 * * * /usr/local/bin/backup-db.sh
0 3 * * * /usr/local/bin/backup-app.sh
```

### Disaster Recovery

1. **Database Recovery**
   ```bash
   # Stop application
   sudo systemctl stop trojan-defender
   
   # Restore database
   gunzip -c backup_20231201_020000.sql.gz | psql -h localhost -U trojan_defender -d trojan_defender
   
   # Start application
   sudo systemctl start trojan-defender
   ```

2. **Full System Recovery**
   ```bash
   # Restore from backup
   tar -xzf media_20231201_030000.tar.gz -C /home/trojan_defender/trojan-defender/backend/
   tar -xzf config_20231201_030000.tar.gz -C /home/trojan_defender/trojan-defender/
   
   # Restore database
   gunzip -c backup_20231201_020000.sql.gz | psql -h localhost -U trojan_defender -d trojan_defender
   
   # Restart services
   sudo systemctl restart trojan-defender
   sudo systemctl restart nginx
   ```

## Performance Optimization

### Database Optimization

1. **Indexing**
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_scans_created_at ON scanner_scan(created_at);
   CREATE INDEX idx_scans_user_id ON scanner_scan(user_id);
   CREATE INDEX idx_threats_severity ON scanner_threat(severity);
   ```

2. **Query Optimization**
   ```python
   # Use select_related and prefetch_related
   scans = Scan.objects.select_related('user').prefetch_related('threats')
   
   # Use database functions
   from django.db.models import Count, Avg
   stats = Scan.objects.aggregate(
       total_scans=Count('id'),
       avg_scan_time=Avg('scan_duration')
   )
   ```

### Caching Strategy

1. **Redis Caching**
   ```python
   # Cache expensive queries
   from django.core.cache import cache
   
   def get_threat_statistics():
       cache_key = 'threat_statistics'
       stats = cache.get(cache_key)
       if stats is None:
           stats = calculate_threat_statistics()
           cache.set(cache_key, stats, 300)  # 5 minutes
       return stats
   ```

2. **CDN Configuration**
   ```nginx
   # Cache static files
   location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
       expires 1y;
       add_header Cache-Control "public, immutable";
   }
   ```

### Application Optimization

1. **Gunicorn Configuration**
   ```python
   # gunicorn.conf.py
   bind = "0.0.0.0:8000"
   workers = 4  # 2 * CPU cores
   worker_class = "gevent"
   worker_connections = 1000
   max_requests = 1000
   max_requests_jitter = 100
   timeout = 30
   keepalive = 5
   ```

2. **Celery Optimization**
   ```python
   # celery.py
   app.conf.update(
       task_serializer='json',
       accept_content=['json'],
       result_serializer='json',
       timezone='UTC',
       enable_utc=True,
       worker_prefetch_multiplier=1,
       task_acks_late=True,
       worker_max_tasks_per_child=1000,
   )
   ```

## Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Optimize PostgreSQL
# Reduce shared_buffers if needed
# Tune work_mem and maintenance_work_mem

# Optimize Redis
# Set maxmemory and maxmemory-policy
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### SSL Certificate Issues
```bash
# Check certificate expiry
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout | grep "Not After"

# Renew certificate
sudo certbot renew --dry-run
sudo certbot renew
```

#### Performance Issues
```bash
# Check system resources
top
htop
iotop

# Check application logs
tail -f /var/log/trojan-defender/app.log

# Check database performance
sudo -u postgres psql -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Monitoring Commands

```bash
# System monitoring
watch -n 1 'free -h && echo && df -h && echo && ps aux --sort=-%cpu | head -10'

# Application monitoring
watch -n 5 'curl -s http://localhost/api/health/ | jq .'

# Database monitoring
watch -n 10 'sudo -u postgres psql -c "SELECT datname, numbackends, xact_commit, xact_rollback FROM pg_stat_database WHERE datname = '"'"'trojan_defender'"'"';"
```

### Log Analysis

```bash
# Analyze nginx logs
sudo tail -f /var/log/nginx/access.log | grep -E "(4[0-9]{2}|5[0-9]{2})"

# Analyze application logs
sudo journalctl -u trojan-defender -f

# Analyze database logs
sudo tail -f /var/log/postgresql/postgresql-*.log | grep ERROR
```

---

*This deployment guide covers production-ready configurations. Always test deployments in a staging environment before applying to production.*