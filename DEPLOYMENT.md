# Deployment Guide

This guide covers deployment options for the SmartOffer Rand Water Salary Calculator.

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
   - [Render](#render)
   - [Heroku](#heroku)
   - [AWS](#aws)
4. [Database Setup](#database-setup)
5. [Environment Configuration](#environment-configuration)
6. [Troubleshooting](#troubleshooting)

## Local Development Setup

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Git

### Steps

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd SmartOffer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On Linux/Mac:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python run_randwater.py
   ```

6. **Access the application**
   - Main application: http://localhost:5001
   - Admin panel: http://localhost:5001/admin/randwater

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Build and start the application**
   ```bash
   docker-compose up -d
   ```

2. **View logs**
   ```bash
   docker-compose logs -f
   ```

3. **Stop the application**
   ```bash
   docker-compose down
   ```

### Manual Docker Commands

1. **Build the Docker image**
   ```bash
   docker build -t randwater-calculator .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     -p 5001:5001 \
     -v $(pwd)/randwater_data.db:/app/randwater_data.db \
     -v $(pwd)/employee_access.json:/app/employee_access.json \
     --name randwater-app \
     randwater-calculator
   ```

3. **Check container status**
   ```bash
   docker ps
   ```

4. **View logs**
   ```bash
   docker logs -f randwater-app
   ```

## Cloud Deployment

### Render

Render is configured via `render.yaml` in the repository.

#### Steps:

1. **Create a Render account** at https://render.com

2. **Connect your GitHub repository**

3. **Render will automatically detect the render.yaml and deploy**

4. **Set environment variables** in Render dashboard:
   - `FLASK_APP=randwater_calculator.py`
   - `FLASK_ENV=production`
   - `PYTHONUNBUFFERED=1`

5. **Deploy**

The application will be available at: `https://your-app-name.onrender.com`

#### Note:
- Free tier may have cold start delays
- Consider upgrading for production use
- Database should be configured separately (PostgreSQL recommended)

### Heroku

#### Steps:

1. **Create a Heroku account** and install Heroku CLI

2. **Login**
   ```bash
   heroku login
   ```

3. **Create a new Heroku app**
   ```bash
   heroku create your-app-name
   ```

4. **Add buildpacks**
   ```bash
   heroku buildpacks:add heroku/python
   ```

5. **Create Procfile** (if not exists):
   ```
   web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 randwater_calculator:app
   ```

6. **Set environment variables**
   ```bash
   heroku config:set FLASK_APP=randwater_calculator.py
   heroku config:set FLASK_ENV=production
   ```

7. **Deploy**
   ```bash
   git push heroku main
   ```

8. **Open the app**
   ```bash
   heroku open
   ```

### AWS (EC2/Elastic Beanstalk)

#### Using AWS Elastic Beanstalk:

1. **Install EB CLI**
   ```bash
   pip install awsebcli
   ```

2. **Initialize Elastic Beanstalk**
   ```bash
   eb init -p python-3.9 randwater-calculator
   ```

3. **Create environment**
   ```bash
   eb create randwater-production
   ```

4. **Deploy**
   ```bash
   eb deploy
   ```

5. **Open the application**
   ```bash
   eb open
   ```

#### Manual EC2 Deployment:

1. **Launch EC2 instance** (Ubuntu recommended)

2. **SSH into the instance**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

3. **Install dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip nginx git
   ```

4. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd SmartOffer
   ```

5. **Set up application** (follow local development setup)

6. **Configure Nginx** as reverse proxy (see example below)

7. **Set up process manager** (PM2 or systemd)

## Database Setup

### SQLite (Default - Development)

The application uses SQLite by default. No additional setup required.

### PostgreSQL (Production)

For production deployments, PostgreSQL is recommended.

#### Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL
sudo service postgresql start
```

#### Create database
```bash
sudo -u postgres psql
CREATE DATABASE randwater_db;
CREATE USER randwater_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE randwater_db TO randwater_user;
\q
```

#### Update application config
Update `config.py` or environment variables:
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://randwater_user:your_password@localhost/randwater_db'
```

## Environment Configuration

### Required Environment Variables

Create a `.env` file or set in your deployment platform:

```bash
FLASK_APP=randwater_calculator.py
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

### Optional Configuration

```bash
# Database
DATABASE_URL=postgresql://user:pass@host/dbname

# Email (if email functionality added)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Security
SECRET_KEY=your-secret-key-here
```

## Nginx Configuration (Reverse Proxy)

Example Nginx configuration for production:

```nginx
upstream randwater_app {
    server 127.0.0.1:5001;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Max upload size
    client_max_body_size 10M;

    location / {
        proxy_pass http://randwater_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files
    location /static {
        alias /path/to/SmartOffer/static;
        expires 30d;
    }
}
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port
lsof -i :5001  # Mac/Linux
netstat -ano | findstr :5001  # Windows

# Kill the process or use different port
```

#### Database Locked
- Ensure no other process is accessing the database
- Check file permissions
- Consider switching to PostgreSQL for production

#### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### Memory Issues
- Reduce Gunicorn workers: `--workers 1`
- Increase swap space
- Consider upgrading server/resources

#### Slow Performance
- Enable caching
- Use PostgreSQL instead of SQLite
- Optimize database queries
- Use CDN for static files

### Logs

#### Docker
```bash
docker logs -f randwater-app
```

#### Local Development
```bash
# Logs appear in console where app is running
# Or check log files in logs/ directory
```

#### Production (Gunicorn)
```bash
tail -f /var/log/gunicorn/error.log
```

## Production Checklist

- [ ] Environment variables configured
- [ ] Database properly configured and backed up
- [ ] SSL certificate installed (for HTTPS)
- [ ] Firewall configured
- [ ] Regular backups scheduled
- [ ] Monitoring set up
- [ ] Error logging configured
- [ ] Performance monitoring enabled
- [ ] Security headers configured
- [ ] Rate limiting enabled (if needed)
- [ ] Static files served efficiently
- [ ] Database indexing optimized

## Support

For deployment assistance, contact the development team.

