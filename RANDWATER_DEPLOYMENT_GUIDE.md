# Rand Water Salary Package Calculator - Deployment Guide

## Overview

This guide explains how to deploy the **Rand Water specific salary calculator** as an iframe within Rand Water's Employee Self-Service (ESS) portal and integrate it with Rand Water's SAP system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Rand Water ESS Portal Integration](#rand-water-ess-portal-integration)
3. [Rand Water SAP Integration Setup](#rand-water-sap-integration-setup)
4. [Deployment Steps](#deployment-steps)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Python 3.8+
- Flask web framework
- Access to Rand Water SAP system
- Rand Water ESS portal with iframe support
- HTTPS certificate (for production)

### Dependencies
Install the Rand Water specific requirements:
```bash
pip install -r requirements_randwater.txt
```

## Rand Water ESS Portal Integration

### 1. iFrame Embedding

Add the Rand Water calculator to your ESS portal using an iframe:

```html
<!-- In Rand Water ESS portal HTML -->
<iframe 
  src="https://calculator.randwater.co.za/calculator?user_id=EMPLOYEE_ID&sso_token=TOKEN" 
  width="100%" 
  height="800px" 
  frameborder="0"
  allow="fullscreen"
  title="Rand Water Salary Package Calculator">
</iframe>
```

### 2. Rand Water SSO Integration

The calculator supports Rand Water specific Single Sign-On (SSO):

```javascript
// In Rand Water ESS portal JavaScript
function openRandWaterCalculator(employeeId) {
  const ssoToken = getRandWaterSSOToken(); // Rand Water SSO token generation
  const calculatorUrl = `https://calculator.randwater.co.za/calculator?user_id=${employeeId}&sso_token=${ssoToken}`;
  
  // Open in iframe or new window
  document.getElementById('randwater-calculator-frame').src = calculatorUrl;
}
```

### 3. Cross-Origin Communication

For communication between Rand Water ESS portal and calculator:

```javascript
// In Rand Water ESS portal
window.addEventListener('message', function(event) {
  if (event.origin !== 'https://calculator.randwater.co.za') return;
  
  if (event.data.type === 'RANDWATER_PACKAGE_SUBMITTED') {
    // Handle Rand Water package submission
    console.log('Rand Water package submitted:', event.data.package);
  }
});

// In calculator (send message to parent)
window.parent.postMessage({
  type: 'RANDWATER_PACKAGE_SUBMITTED',
  package: packageData,
  company: 'RANDWATER'
}, 'https://ess.randwater.co.za');
```

## Rand Water SAP Integration Setup

### 1. Rand Water SAP Connection Configuration

Create a `.env` file with Rand Water SAP credentials:

```env
# Rand Water SAP Configuration
RANDWATER_SAP_URL=https://sap.randwater.co.za
RANDWATER_SAP_USER=randwater_sap_user
RANDWATER_SAP_PASS=randwater_sap_password
RANDWATER_SAP_CLIENT=100

# Rand Water ESS Integration
RANDWATER_ESS_VALIDATION_URL=https://ess.randwater.co.za/validate-token
RANDWATER_ESS_API_KEY=randwater_ess_api_key

# Application Settings
SECRET_KEY=randwater-super-secret-key-2024
DEBUG=False
LOG_LEVEL=INFO
```

### 2. Rand Water SAP Data Mapping

Configure the data mapping between Rand Water SAP and the calculator:

```python
# In randwater_calculator.py - Rand Water specific mappings
RANDWATER_SAP_FIELD_MAPPING = {
    'employee_id': 'PERNR',
    'first_name': 'VORNA',
    'surname': 'NACHN',
    'basic_salary': 'BASIC_SALARY',
    'department': 'ORGEH',
    'job_title': 'PLANS',
    'randwater_benefits': 'RW_BENEFITS'
}
```

### 3. Rand Water SAP RFC Functions

The integration uses these Rand Water specific SAP RFC functions:

- **BAPI_RW_EMPLOYEE_GETDATA**: Get Rand Water employee master data
- **BAPI_RW_SALARY_GETDATA**: Get Rand Water salary information
- **BAPI_RW_PACKAGE_UPDATE**: Submit Rand Water package changes
- **BAPI_RW_BENEFITS_GETDATA**: Get Rand Water specific benefits

## Deployment Steps

### 1. Rand Water Application Deployment

#### Option A: Traditional Server
```bash
# Clone the repository
git clone <randwater-repo-url>
cd randwater-calculator

# Install Rand Water specific dependencies
pip install -r requirements_randwater.txt

# Set Rand Water environment variables
export FLASK_ENV=production
export RANDWATER_SAP_URL=https://sap.randwater.co.za
export RANDWATER_SAP_USER=randwater_sap_user
export RANDWATER_SAP_PASS=randwater_sap_password
# ... other Rand Water environment variables

# Run with Gunicorn on port 5001 (different from main calculator)
gunicorn -w 4 -b 0.0.0.0:5001 randwater_calculator:app
```

#### Option B: Docker Deployment
```dockerfile
# Dockerfile for Rand Water
FROM python:3.9-slim

WORKDIR /app
COPY requirements_randwater.txt .
RUN pip install -r requirements_randwater.txt

COPY . .
EXPOSE 5001

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "randwater_calculator:app"]
```

```bash
# Build and run Rand Water calculator
docker build -t randwater-calculator .
docker run -p 5001:5001 --env-file .env randwater-calculator
```

#### Option C: Cloud Deployment (AWS, Azure, GCP)
```yaml
# docker-compose.yml for Rand Water
version: '3.8'
services:
  randwater-calculator:
    build: .
    ports:
      - "5001:5001"
    environment:
      - FLASK_ENV=production
      - COMPANY=RANDWATER
    env_file:
      - .env
    volumes:
      - ./exports:/app/exports
      - ./uploads:/app/uploads
```

### 2. Reverse Proxy Setup (Nginx)

```nginx
# /etc/nginx/sites-available/randwater-calculator
server {
    listen 80;
    server_name calculator.randwater.co.za;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name calculator.randwater.co.za;
    
    ssl_certificate /path/to/randwater/certificate.crt;
    ssl_certificate_key /path/to/randwater/private.key;
    
    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers for Rand Water ESS
        add_header Access-Control-Allow-Origin "https://ess.randwater.co.za";
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
}
```

### 3. SSL Certificate Setup

```bash
# Using Let's Encrypt for Rand Water domain
sudo certbot --nginx -d calculator.randwater.co.za
```

## Configuration

### 1. Rand Water Environment Variables

Create a production `.env` file for Rand Water:

```env
# Rand Water Production Configuration
FLASK_ENV=production
SECRET_KEY=randwater-super-secure-secret-key-2024
DEBUG=False

# Rand Water SAP Integration
RANDWATER_SAP_URL=https://sap.randwater.co.za
RANDWATER_SAP_USER=randwater_sap_user
RANDWATER_SAP_PASS=randwater_sap_password
RANDWATER_SAP_CLIENT=100

# Rand Water ESS Integration
RANDWATER_ESS_VALIDATION_URL=https://ess.randwater.co.za/validate-token
RANDWATER_ESS_API_KEY=randwater_ess_api_key

# Rand Water File Storage
EXPORT_DIR=/var/www/randwater/exports
UPLOAD_DIR=/var/www/randwater/uploads

# Rand Water Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/randwater-calculator/app.log
```

### 2. Rand Water Database Setup (Optional)

For production, consider using a database for Rand Water packages:

```python
# In randwater_calculator.py
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/randwater_calc'
db = SQLAlchemy(app)

class RandWaterPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), nullable=False)
    package_data = db.Column(db.JSON)
    status = db.Column(db.String(20), default='DRAFT')
    company = db.Column(db.String(20), default='RANDWATER')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 3. Rand Water Security Configuration

```python
# Security headers for Rand Water
from flask_talisman import Talisman

Talisman(app, 
    content_security_policy={
        'default-src': ["'self'"],
        'frame-ancestors': ["'self'", "https://ess.randwater.co.za"],
        'script-src': ["'self'", "'unsafe-inline'"],
        'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        'font-src': ["'self'", "https://fonts.gstatic.com"]
    }
)
```

## Testing

### 1. Rand Water Unit Tests

```bash
# Run Rand Water specific tests
python -m pytest tests/test_randwater.py
```

### 2. Rand Water Integration Tests

```python
# test_randwater_sap_integration.py
def test_randwater_sap_employee_data():
    sap = RandWaterSAPIntegration(RANDWATER_CONFIG['sap_config'])
    data = sap.get_employee_data('RW001')
    assert data is not None
    assert 'employee_id' in data
    assert data.get('company') == 'RANDWATER'
```

### 3. Rand Water End-to-End Testing

```bash
# Test Rand Water iframe integration
curl -H "X-SSO-Token: randwater-test-token" \
     -H "X-User-ID: RW001" \
     https://calculator.randwater.co.za/api/randwater/employee/RW001
```

## Troubleshooting

### Common Rand Water Issues

#### 1. CORS Errors with Rand Water ESS
```nginx
# Add to Nginx configuration for Rand Water
add_header Access-Control-Allow-Origin "https://ess.randwater.co.za";
add_header Access-Control-Allow-Credentials "true";
```

#### 2. Rand Water SAP Connection Issues
```python
# Test Rand Water SAP connection
import requests

def test_randwater_sap_connection():
    try:
        response = requests.get(f"{RANDWATER_SAP_URL}/sap/opu/odata/sap/ZRW_EMPLOYEE_SRV/EmployeeSet", 
                              auth=(RANDWATER_SAP_USER, RANDWATER_SAP_PASS), 
                              timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Rand Water SAP connection failed: {e}")
        return False
```

#### 3. Rand Water iFrame Display Issues
```css
/* Ensure proper Rand Water iframe sizing */
.randwater-calculator-iframe {
    width: 100%;
    height: 800px;
    border: none;
    overflow: hidden;
}
```

### Rand Water Logging and Monitoring

```python
# Enhanced logging for Rand Water
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/randwater_calculator.log', 
                                     maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Rand Water Salary Calculator startup')
```

## Performance Optimization

### 1. Rand Water Caching
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.memoize(timeout=300)
def get_randwater_employee_data(employee_id):
    return randwater_sap.get_employee_data(employee_id)
```

### 2. Rand Water Database Optimization
```sql
-- Create indexes for Rand Water packages
CREATE INDEX idx_randwater_package_employee_id ON randwater_packages(employee_id);
CREATE INDEX idx_randwater_package_status ON randwater_packages(status);
CREATE INDEX idx_randwater_package_company ON randwater_packages(company);
```

## Security Considerations

1. **HTTPS Only**: Always use HTTPS for Rand Water production
2. **Input Validation**: Validate all Rand Water user inputs
3. **SQL Injection**: Use parameterized queries for Rand Water data
4. **XSS Protection**: Sanitize Rand Water user inputs
5. **CSRF Protection**: Implement CSRF tokens for Rand Water
6. **Rate Limiting**: Limit API requests per Rand Water user

## Rand Water Maintenance

### Regular Tasks
- Monitor Rand Water log files for errors
- Backup Rand Water package data regularly
- Update Rand Water dependencies monthly
- Review Rand Water SAP connection logs
- Monitor Rand Water system performance

### Updates
```bash
# Update Rand Water application
git pull origin main
pip install -r requirements_randwater.txt
sudo systemctl restart randwater-calculator
```

## Rand Water Specific Features

### 1. Rand Water Benefits
- Water Allowance
- Infrastructure Bonus
- Environmental Incentive
- Rand Water specific deductions

### 2. Rand Water Branding
- Rand Water logo and colors
- Rand Water specific terminology
- Rand Water branded PDFs and reports

### 3. Rand Water SAP Integration
- Rand Water specific SAP endpoints
- Rand Water employee data mapping
- Rand Water package submission workflow

This deployment guide provides a comprehensive approach to deploying the Rand Water specific salary calculator with both the Rand Water ESS portal and SAP system. Follow the steps carefully and test thoroughly in a staging environment before going live. 