# Salary Calculator - ESS Portal Integration & SAP Deployment Guide

## Overview

This guide explains how to deploy the salary calculator as an iframe within your company's Employee Self-Service (ESS) portal and integrate it with SAP for data exchange.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [ESS Portal Integration](#ess-portal-integration)
3. [SAP Integration Setup](#sap-integration-setup)
4. [Deployment Steps](#deployment-steps)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Python 3.8+
- Flask web framework
- Access to SAP system (for data integration)
- ESS portal with iframe support
- HTTPS certificate (for production)

### Dependencies
Install the enhanced requirements:
```bash
pip install -r requirements_enhanced.txt
```

## ESS Portal Integration

### 1. iFrame Embedding

Add the calculator to your ESS portal using an iframe:

```html
<!-- In your ESS portal HTML -->
<iframe 
  src="https://your-calculator-domain.com/calculator/iframe?user_id=EMPLOYEE_ID&sso_token=TOKEN" 
  width="100%" 
  height="800px" 
  frameborder="0"
  allow="fullscreen"
  title="Salary Package Calculator">
</iframe>
```

### 2. SSO Integration

The calculator supports Single Sign-On (SSO) integration:

```javascript
// In your ESS portal JavaScript
function openCalculator(employeeId) {
  const ssoToken = getSSOToken(); // Your SSO token generation
  const calculatorUrl = `https://your-calculator-domain.com/calculator/iframe?user_id=${employeeId}&sso_token=${ssoToken}`;
  
  // Open in iframe or new window
  document.getElementById('calculator-frame').src = calculatorUrl;
}
```

### 3. Cross-Origin Communication

For communication between ESS portal and calculator:

```javascript
// In ESS portal
window.addEventListener('message', function(event) {
  if (event.origin !== 'https://your-calculator-domain.com') return;
  
  if (event.data.type === 'PACKAGE_SUBMITTED') {
    // Handle package submission
    console.log('Package submitted:', event.data.package);
  }
});

// In calculator (send message to parent)
window.parent.postMessage({
  type: 'PACKAGE_SUBMITTED',
  package: packageData
}, 'https://your-ess-domain.com');
```

## SAP Integration Setup

### 1. SAP Connection Configuration

Create a `.env` file with your SAP credentials:

```env
# SAP Configuration
SAP_BASE_URL=https://your-sap-system.com
SAP_USERNAME=your_sap_username
SAP_PASSWORD=your_sap_password
SAP_CLIENT=100

# ESS Integration
ESS_VALIDATION_URL=https://your-ess-system.com/validate-token
ESS_API_KEY=your_ess_api_key

# Application Settings
SECRET_KEY=your-super-secret-key
DEBUG=False
LOG_LEVEL=INFO
```

### 2. SAP Data Mapping

Configure the data mapping between SAP and the calculator:

```python
# In sap_integration.py - customize these mappings
SAP_FIELD_MAPPING = {
    'employee_id': 'PERNR',
    'first_name': 'VORNA',
    'surname': 'NACHN',
    'basic_salary': 'BASIC_SALARY',
    'department': 'ORGEH',
    'job_title': 'PLANS'
}
```

### 3. SAP RFC Functions

The integration uses these SAP RFC functions:

- **BAPI_EMPLOYEE_GETDATA**: Get employee master data
- **BAPI_SALARY_GETDATA**: Get salary information
- **BAPI_PACKAGE_UPDATE**: Submit package changes

## Deployment Steps

### 1. Application Deployment

#### Option A: Traditional Server
```bash
# Clone the repository
git clone <your-repo-url>
cd the-negotiator

# Install dependencies
pip install -r requirements_enhanced.txt

# Set environment variables
export FLASK_ENV=production
export SAP_BASE_URL=https://your-sap-system.com
# ... other environment variables

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app_enhanced:app
```

#### Option B: Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements_enhanced.txt .
RUN pip install -r requirements_enhanced.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app_enhanced:app"]
```

```bash
# Build and run
docker build -t salary-calculator .
docker run -p 5000:5000 --env-file .env salary-calculator
```

#### Option C: Cloud Deployment (AWS, Azure, GCP)
```yaml
# docker-compose.yml
version: '3.8'
services:
  calculator:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    env_file:
      - .env
    volumes:
      - ./exports:/app/exports
      - ./uploads:/app/uploads
```

### 2. Reverse Proxy Setup (Nginx)

```nginx
# /etc/nginx/sites-available/salary-calculator
server {
    listen 80;
    server_name your-calculator-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-calculator-domain.com;
    
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers for iframe
        add_header Access-Control-Allow-Origin "https://your-ess-domain.com";
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
}
```

### 3. SSL Certificate Setup

```bash
# Using Let's Encrypt
sudo certbot --nginx -d your-calculator-domain.com
```

## Configuration

### 1. Environment Variables

Create a production `.env` file:

```env
# Production Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secure-secret-key
DEBUG=False

# SAP Integration
SAP_BASE_URL=https://your-sap-system.com
SAP_USERNAME=your_sap_username
SAP_PASSWORD=your_sap_password
SAP_CLIENT=100

# ESS Integration
ESS_VALIDATION_URL=https://your-ess-system.com/validate-token
ESS_API_KEY=your_ess_api_key

# File Storage
EXPORT_DIR=/var/www/exports
UPLOAD_DIR=/var/www/uploads

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/salary-calculator/app.log
```

### 2. Database Setup (Optional)

For production, consider using a database instead of file storage:

```python
# In app_enhanced.py
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/salary_calc'
db = SQLAlchemy(app)

class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), nullable=False)
    package_data = db.Column(db.JSON)
    status = db.Column(db.String(20), default='DRAFT')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 3. Security Configuration

```python
# Security headers
from flask_talisman import Talisman

Talisman(app, 
    content_security_policy={
        'default-src': ["'self'"],
        'frame-ancestors': ["'self'", "https://your-ess-domain.com"],
        'script-src': ["'self'", "'unsafe-inline'"],
        'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        'font-src': ["'self'", "https://fonts.gstatic.com"]
    }
)
```

## Testing

### 1. Unit Tests

```bash
# Run tests
python -m pytest tests/
```

### 2. Integration Tests

```python
# test_sap_integration.py
def test_sap_employee_data():
    sap = SAPIntegration(SAP_CONFIG)
    data = sap.get_employee_data('TEST001')
    assert data is not None
    assert 'employee_id' in data
```

### 3. End-to-End Testing

```bash
# Test iframe integration
curl -H "X-SSO-Token: test-token" \
     -H "X-User-ID: TEST001" \
     https://your-calculator-domain.com/api/employee/TEST001
```

## Troubleshooting

### Common Issues

#### 1. CORS Errors
```nginx
# Add to Nginx configuration
add_header Access-Control-Allow-Origin "https://your-ess-domain.com";
add_header Access-Control-Allow-Credentials "true";
```

#### 2. SAP Connection Issues
```python
# Test SAP connection
import requests

def test_sap_connection():
    try:
        response = requests.get(f"{SAP_BASE_URL}/sap/opu/odata/sap/ZHR_EMPLOYEE_SRV/EmployeeSet", 
                              auth=(SAP_USERNAME, SAP_PASSWORD), 
                              timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"SAP connection failed: {e}")
        return False
```

#### 3. iFrame Display Issues
```css
/* Ensure proper iframe sizing */
.calculator-iframe {
    width: 100%;
    height: 800px;
    border: none;
    overflow: hidden;
}
```

### Logging and Monitoring

```python
# Enhanced logging
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/salary_calculator.log', 
                                     maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Salary Calculator startup')
```

## Performance Optimization

### 1. Caching
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.memoize(timeout=300)
def get_employee_data(employee_id):
    return sap_integration.get_employee_data(employee_id)
```

### 2. Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_package_employee_id ON packages(employee_id);
CREATE INDEX idx_package_status ON packages(status);
CREATE INDEX idx_package_created_at ON packages(created_at);
```

## Security Considerations

1. **HTTPS Only**: Always use HTTPS in production
2. **Input Validation**: Validate all user inputs
3. **SQL Injection**: Use parameterized queries
4. **XSS Protection**: Sanitize user inputs
5. **CSRF Protection**: Implement CSRF tokens
6. **Rate Limiting**: Limit API requests per user

## Maintenance

### Regular Tasks
- Monitor log files for errors
- Backup package data regularly
- Update dependencies monthly
- Review SAP connection logs
- Monitor system performance

### Updates
```bash
# Update application
git pull origin main
pip install -r requirements_enhanced.txt
sudo systemctl restart salary-calculator
```

This deployment guide provides a comprehensive approach to integrating your salary calculator with both the ESS portal and SAP system. Follow the steps carefully and test thoroughly in a staging environment before going live. 