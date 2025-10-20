# Golf2025 Deployment Guide

**Version:** 1.0
**Last Updated:** 2025-10-20

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Production Deployment](#production-deployment)
4. [Environment Variables](#environment-variables)
5. [Database Setup](#database-setup)
6. [Static Files](#static-files)
7. [Security Checklist](#security-checklist)
8. [Monitoring](#monitoring)
9. [Backup Strategy](#backup-strategy)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Python:** 3.11+
- **Node.js:** 18+ (for frontend builds)
- **Database:** PostgreSQL 14+ (recommended) or SQLite (development only)
- **Web Server:** Nginx or Apache
- **WSGI Server:** Gunicorn or uWSGI
- **OS:** Ubuntu 22.04 LTS (recommended) or similar Linux distribution

### Required Services

- **Redis:** For caching and session storage (optional but recommended)
- **Celery:** For background tasks (if needed)
- **Email Server:** For sending notifications

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/golf2025.git
cd golf2025
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Node.js dependencies
npm install
```

### 4. Build Frontend Assets

```bash
# Build custom Bootstrap CSS
npm run build:css

# Run frontend tests
npm test
```

---

## Production Deployment

### Option 1: Traditional Server Deployment

#### Step 1: Configure Environment Variables

Create `.env` file in project root:

```bash
# .env
DEBUG=False
SECRET_KEY=your-very-secret-key-here-min-50-chars
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost:5432/golf2025
REDIS_URL=redis://localhost:6379/0

# Email settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (for media files - optional)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Support
SUPPORT_EMAIL=support@yourdomain.com
```

#### Step 2: Set Up Database

```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE golf2025;
CREATE USER golf2025user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE golf2025 TO golf2025user;
\q

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (if any)
python manage.py loaddata initial_data.json
```

#### Step 3: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

#### Step 4: Configure Gunicorn

Create `/etc/systemd/system/golf2025.service`:

```ini
[Unit]
Description=Golf2025 Gunicorn Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/golf2025
Environment="PATH=/var/www/golf2025/venv/bin"
ExecStart=/var/www/golf2025/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/golf2025/golf2025.sock \
    --access-logfile /var/log/golf2025/access.log \
    --error-logfile /var/log/golf2025/error.log \
    golf2025.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl start golf2025
sudo systemctl enable golf2025
sudo systemctl status golf2025
```

#### Step 5: Configure Nginx

Create `/etc/nginx/sites-available/golf2025`:

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

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Logs
    access_log /var/log/nginx/golf2025_access.log;
    error_log /var/log/nginx/golf2025_error.log;

    # Static files
    location /static/ {
        alias /var/www/golf2025/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/golf2025/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://unix:/var/www/golf2025/golf2025.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/golf2025 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Step 6: SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Option 2: Docker Deployment

#### Dockerfile

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "golf2025.wsgi:application"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    command: gunicorn golf2025.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    expose:
      - 8000
    env_file:
      - .env
    depends_on:
      - db

  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=golf2025
      - POSTGRES_USER=golf2025user
      - POSTGRES_PASSWORD=your-password

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

---

## Environment Variables

### Required Variables

```bash
# Core settings
DEBUG=False  # MUST be False in production
SECRET_KEY=  # Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password

# Support
SUPPORT_EMAIL=support@yourdomain.com
```

### Optional Variables

```bash
# Redis (caching)
REDIS_URL=redis://localhost:6379/0

# AWS S3 (media storage)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=us-east-1

# Logging
LOG_REQUESTS=False
```

---

## Database Setup

### PostgreSQL (Recommended)

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb golf2025
sudo -u postgres createuser golf2025user

# Set password
sudo -u postgres psql
ALTER USER golf2025user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE golf2025 TO golf2025user;
\q

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://golf2025user:your-password@localhost:5432/golf2025

# Run migrations
python manage.py migrate
```

### Backup and Restore

```bash
# Backup
pg_dump golf2025 > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
psql golf2025 < backup_20251020_120000.sql
```

---

## Static Files

### Development

```bash
python manage.py collectstatic
```

### Production (S3)

Install dependencies:

```bash
pip install boto3 django-storages
```

Update `settings.py`:

```python
if not DEBUG:
    # AWS S3 settings
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_DEFAULT_ACL = 'public-read'

    # Static files
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

    # Media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
```

---

## Security Checklist

### Pre-Deployment

- [ ] `DEBUG = False`
- [ ] Strong `SECRET_KEY` (min 50 characters)
- [ ] `ALLOWED_HOSTS` configured
- [ ] Database password is strong
- [ ] SSL certificate installed
- [ ] Security headers configured in Nginx
- [ ] CSRF protection enabled
- [ ] XSS protection enabled
- [ ] SQL injection protection (use ORM)
- [ ] File upload validation
- [ ] Rate limiting configured
- [ ] HTTPS enforced

### Django Security Settings

```python
# settings.py (production)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

## Monitoring

### Application Monitoring

**Recommended tools:**
- Sentry - Error tracking
- New Relic - Performance monitoring
- DataDog - Full-stack monitoring

### Log Monitoring

```bash
# View application logs
tail -f /var/log/golf2025/golf2025.log

# View error logs
tail -f /var/log/golf2025/errors.log

# View Nginx logs
tail -f /var/log/nginx/golf2025_access.log
tail -f /var/log/nginx/golf2025_error.log
```

### Health Checks

Create a health check endpoint:

```python
# views.py
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'healthy'})
```

Monitor with:

```bash
curl https://yourdomain.com/health/
```

---

## Backup Strategy

### Automated Backups

Create backup script `/usr/local/bin/backup-golf2025.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/golf2025"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
pg_dump golf2025 | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Backup media files
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" /var/www/golf2025/media

# Keep only last 30 days
find "$BACKUP_DIR" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 sync "$BACKUP_DIR" s3://your-backup-bucket/golf2025/
```

Add to crontab:

```bash
# Run daily at 2 AM
0 2 * * * /usr/local/bin/backup-golf2025.sh
```

---

## Troubleshooting

### Common Issues

#### 1. Static files not loading

```bash
# Collect static files
python manage.py collectstatic --noinput

# Check Nginx configuration
sudo nginx -t

# Check file permissions
ls -la /var/www/golf2025/staticfiles
```

#### 2. Database connection errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U golf2025user -d golf2025 -h localhost

# Check DATABASE_URL in .env
```

#### 3. Gunicorn not starting

```bash
# Check service status
sudo systemctl status golf2025

# View logs
sudo journalctl -u golf2025 -n 50

# Test Gunicorn manually
gunicorn --bind 0.0.0.0:8000 golf2025.wsgi:application
```

#### 4. Permission errors

```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/golf2025

# Fix permissions
find /var/www/golf2025 -type d -exec chmod 755 {} \;
find /var/www/golf2025 -type f -exec chmod 644 {} \;
```

---

## Support

For deployment issues:
- Email: support@yourdomain.com
- Documentation: https://docs.yourdomain.com
- GitHub Issues: https://github.com/your-org/golf2025/issues

---

**Last Updated:** 2025-10-20
**Version:** 1.0
