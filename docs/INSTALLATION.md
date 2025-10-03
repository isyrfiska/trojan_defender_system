# Installation Guide

This guide provides detailed instructions for installing and setting up Trojan Defender in various environments.

## Table of Contents

- [System Requirements](#system-requirements)
- [Docker Installation (Recommended)](#docker-installation-recommended)
- [Manual Installation](#manual-installation)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Initial Data Population](#initial-data-population)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows 10+
- **RAM**: 4GB (8GB recommended)
- **Storage**: 10GB free space
- **Network**: Internet connection for updates and threat intelligence

### Software Dependencies
- **Docker**: 20.10+ and Docker Compose 2.0+
- **Python**: 3.9+ (for manual installation)
- **Node.js**: 16+ (for manual installation)
- **PostgreSQL**: 13+ (for production)

## Docker Installation (Recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/trojan_defender.git
cd trojan_defender
```

### 2. Environment Setup

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```bash
# Basic Configuration
DEBUG=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database (PostgreSQL for production)
DATABASE_URL=postgresql://trojan_user:password@db:5432/trojan_defender

# Redis for Celery
REDIS_URL=redis://redis:6379/0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# OpenAI for Chatbot
OPENAI_API_KEY=your-openai-api-key

# Security
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://your-domain.com
```

### 3. Deploy with Docker Compose

#### Development Environment

```bash
docker-compose up -d
```

#### Production Environment

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Initialize the Application

```bash
# Run database migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Populate initial data
docker-compose exec backend python populate_chatbot_data.py

# Update ClamAV signatures
docker-compose exec backend freshclam
```

### 5. Verify Installation

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/swagger/

## Manual Installation

### Backend Setup

1. **Create Virtual Environment**
   ```bash
   cd backend
   python -m venv venv
   
   # On Linux/macOS
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install System Dependencies**
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install clamav clamav-daemon redis-server postgresql
   ```
   
   **CentOS/RHEL:**
   ```bash
   sudo yum install epel-release
   sudo yum install clamav clamav-update redis postgresql-server
   ```
   
   **macOS:**
   ```bash
   brew install clamav redis postgresql
   ```

4. **Configure Database**
   ```bash
   # Create database
   sudo -u postgres createdb trojan_defender
   sudo -u postgres createuser trojan_user
   sudo -u postgres psql -c "ALTER USER trojan_user WITH PASSWORD 'password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE trojan_defender TO trojan_user;"
   ```

5. **Run Migrations**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Start Services**
   ```bash
   # Start Redis
   redis-server
   
   # Start Celery Worker
   celery -A trojan_defender worker -l info
   
   # Start Django Server
   python manage.py runserver
   ```

### Frontend Setup

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env.local
   ```
   
   Edit `.env.local`:
   ```bash
   VITE_API_URL=http://localhost:8000
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```

## Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Allowed hostnames | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `EMAIL_HOST` | SMTP server | `smtp.gmail.com` |
| `EMAIL_HOST_USER` | Email username | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | Email password | `your-app-password` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_USE_TLS` | Use TLS | `True` |
| `CELERY_BROKER_URL` | Celery broker | Same as `REDIS_URL` |
| `MAX_UPLOAD_SIZE` | Max file size (MB) | `100` |
| `SCAN_TIMEOUT` | Scan timeout (seconds) | `300` |

## Database Setup

### PostgreSQL (Production)

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # CentOS/RHEL
   sudo yum install postgresql-server postgresql-contrib
   
   # macOS
   brew install postgresql
   ```

2. **Create Database and User**
   ```sql
   sudo -u postgres psql
   CREATE DATABASE trojan_defender;
   CREATE USER trojan_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE trojan_defender TO trojan_user;
   ALTER USER trojan_user CREATEDB;
   \q
   ```

3. **Configure Connection**
   Update `DATABASE_URL` in your `.env` file:
   ```bash
   DATABASE_URL=postgresql://trojan_user:secure_password@localhost:5432/trojan_defender
   ```

### SQLite (Development)

For development, you can use SQLite (default):
```bash
DATABASE_URL=sqlite:///db.sqlite3
```

## Initial Data Population

After installation, populate the database with initial data:

```bash
# Populate security topics and resources
python populate_chatbot_data.py

# Create test user (optional)
python create_test_user.py
```

## Troubleshooting

### Common Issues

#### 1. ClamAV Not Starting
```bash
# Update virus definitions
sudo freshclam

# Start ClamAV daemon
sudo systemctl start clamav-daemon
sudo systemctl enable clamav-daemon
```

#### 2. Redis Connection Error
```bash
# Start Redis server
sudo systemctl start redis
sudo systemctl enable redis

# Check Redis status
redis-cli ping
```

#### 3. Database Connection Error
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### 4. Permission Errors
```bash
# Fix file permissions
sudo chown -R $USER:$USER /path/to/trojan_defender
chmod +x deploy.sh
```

#### 5. Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

### Docker Issues

#### 1. Container Won't Start
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 2. Volume Permission Issues
```bash
# Fix volume permissions
sudo chown -R 1000:1000 ./media
sudo chown -R 1000:1000 ./logs
```

### Getting Help

- **Documentation**: Check other files in the `docs/` directory
- **Logs**: Check application logs in `backend/logs/`
- **Issues**: Report problems on GitHub Issues
- **Community**: Join our Discord server for support

## Next Steps

After successful installation:

1. Read the [User Guide](USER_GUIDE.md) to learn how to use the application
2. Check the [Security Guide](SECURITY.md) for security best practices
3. Review the [API Documentation](API.md) for integration details
4. See the [Deployment Guide](DEPLOYMENT.md) for production deployment