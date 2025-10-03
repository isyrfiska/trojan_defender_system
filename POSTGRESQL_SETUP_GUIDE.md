# PostgreSQL Setup Guide for Trojan Defender

This guide will help you set up PostgreSQL for the Trojan Defender application on Windows.

## Prerequisites

- Windows 10/11
- Administrator privileges
- Python 3.8+ with pip

## Step 1: Install PostgreSQL

### Option A: Download from Official Website (Recommended)

1. Go to https://www.postgresql.org/download/windows/
2. Download PostgreSQL 14 or 15 (recommended versions)
3. Run the installer as Administrator
4. During installation:
   - Set a strong password for the `postgres` superuser (remember this!)
   - Use default port `5432`
   - Select default locale
   - Install pgAdmin 4 (optional but recommended)

### Option B: Using Chocolatey (if you have it)

```powershell
# Run as Administrator
choco install postgresql
```

### Option C: Using Scoop (if you have it)

```powershell
scoop install postgresql
```

## Step 2: Verify PostgreSQL Installation

1. Open Command Prompt as Administrator
2. Check if PostgreSQL service is running:

```cmd
sc query postgresql-x64-14
```

3. If not running, start the service:

```cmd
net start postgresql-x64-14
```

4. Test connection:

```cmd
psql -U postgres -h localhost
```

## Step 3: Configure PostgreSQL for Trojan Defender

### Method 1: Automatic Setup (Recommended)

1. Navigate to the backend directory:

```cmd
cd C:\Users\isyra\trojan_defender-main\backend
```

2. Activate your virtual environment:

```cmd
.venv\Scripts\activate
```

3. Run the setup script:

```cmd
python setup_postgresql.py
```

4. Follow the prompts and enter your PostgreSQL superuser password when asked.

### Method 2: Manual Setup

1. Connect to PostgreSQL as superuser:

```cmd
psql -U postgres -h localhost
```

2. Create the database and user:

```sql
-- Create user
CREATE USER trojan_defender_user WITH PASSWORD 'TrojanDefender2024!SecurePass';

-- Create database
CREATE DATABASE trojan_defender_db OWNER trojan_defender_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE trojan_defender_db TO trojan_defender_user;
ALTER USER trojan_defender_user CREATEDB;

-- Exit
\q
```

## Step 4: Test the Configuration

1. Run the database test script:

```cmd
python test_database_config.py
```

2. If all tests pass, run Django migrations:

```cmd
python manage.py makemigrations
python manage.py migrate
```

3. Create a superuser (optional):

```cmd
python manage.py createsuperuser
```

## Step 5: Migrate Existing Data (if applicable)

If you have existing data in SQLite, run the migration script:

```cmd
python migrate_sqlite_to_postgresql.py
```

## Troubleshooting

### PostgreSQL Service Not Running

```cmd
# Check service status
sc query postgresql-x64-14

# Start service
net start postgresql-x64-14

# If service doesn't exist, try:
net start postgresql-x64-15
# or
net start postgresql
```

### Connection Refused Error

1. Check if PostgreSQL is listening on port 5432:

```cmd
netstat -an | findstr 5432
```

2. Check PostgreSQL configuration file (`postgresql.conf`):
   - Usually located in: `C:\Program Files\PostgreSQL\14\data\`
   - Ensure `listen_addresses = 'localhost'`
   - Ensure `port = 5432`

3. Check client authentication file (`pg_hba.conf`):
   - Add line: `host all all 127.0.0.1/32 md5`

4. Restart PostgreSQL service after changes:

```cmd
net stop postgresql-x64-14
net start postgresql-x64-14
```

### Authentication Failed

1. Reset postgres user password:

```cmd
# Stop PostgreSQL service
net stop postgresql-x64-14

# Start in single-user mode (run as Administrator)
"C:\Program Files\PostgreSQL\14\bin\postgres.exe" --single -D "C:\Program Files\PostgreSQL\14\data" postgres

# In the single-user session:
ALTER USER postgres PASSWORD 'your_new_password';

# Exit and restart service
net start postgresql-x64-14
```

### Permission Denied

1. Ensure you're running commands as Administrator
2. Check Windows Firewall settings for port 5432
3. Verify PostgreSQL data directory permissions

## Environment Variables

The following environment variables are configured in `backend/.env`:

```env
# Database Configuration - PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=trojan_defender_db
DB_USER=trojan_defender_user
DB_PASSWORD=TrojanDefender2024!SecurePass
DB_HOST=localhost
DB_PORT=5432

# Database Connection Pooling
DB_CONN_MAX_AGE=600
DB_CONN_HEALTH_CHECKS=True
DB_OPTIONS_sslmode=prefer
DB_OPTIONS_statement_timeout=30000
```

## Security Considerations

1. **Change Default Passwords**: Always change the default PostgreSQL passwords
2. **Firewall Rules**: Configure Windows Firewall to restrict PostgreSQL access
3. **SSL/TLS**: Enable SSL for production deployments
4. **Regular Backups**: Set up automated database backups
5. **User Privileges**: Use principle of least privilege for database users

## Production Deployment

For production deployment, consider:

1. **Dedicated Database Server**: Use a separate server for PostgreSQL
2. **Connection Pooling**: Configure pgBouncer for connection pooling
3. **Monitoring**: Set up PostgreSQL monitoring and alerting
4. **High Availability**: Configure PostgreSQL clustering or replication
5. **Performance Tuning**: Optimize PostgreSQL configuration for your workload

## Docker Alternative

If you prefer using Docker, you can use the provided `docker-compose.yml`:

```cmd
# Start PostgreSQL with Docker
docker-compose up db -d

# Check if it's running
docker-compose ps
```

## Support

If you encounter issues:

1. Check the PostgreSQL logs: `C:\Program Files\PostgreSQL\14\data\log\`
2. Review Django logs in `backend/logs/`
3. Run the test script for detailed diagnostics: `python test_database_config.py`

## Next Steps

After successful setup:

1. Start the Django development server: `python manage.py runserver 8000`
2. Access the admin panel: http://localhost:8000/admin/
3. Test the application functionality
4. Run the complete test suite: `python manage.py test`