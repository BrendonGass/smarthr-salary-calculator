# Rand Water Salary Package Calculator

## Overview

A **dedicated salary package calculator** specifically designed for Rand Water employees, featuring ESS portal integration and SAP data exchange capabilities.

## Features

### 🏢 **Rand Water Specific Features**
- **Rand Water Branding**: Custom styling with Rand Water colors and logo
- **Rand Water Benefits**: Water Allowance, Infrastructure Bonus, Environmental Incentive
- **Rand Water SAP Integration**: Direct connection to Rand Water's SAP system
- **Rand Water ESS Portal**: Seamless integration with Rand Water's Employee Self-Service portal

### 💰 **Salary Package Management**
- **SAP Data Pull**: Load current employee data from Rand Water SAP
- **Package Structuring**: Add/modify allowances and deductions
- **Field Locking**: Lock SAP data while allowing custom additions
- **Real-time Calculations**: SARS-compliant tax calculations
- **Package Submission**: Submit completed packages back to Rand Water SAP

### 📊 **ESS Portal Integration**
- **iFrame Ready**: Designed for seamless ESS portal embedding
- **SSO Support**: Single Sign-On integration with Rand Water ESS
- **Cross-Origin Communication**: Secure messaging between ESS and calculator
- **Responsive Design**: Works on desktop and mobile devices

### 🖨️ **Document Generation**
- **Rand Water Branded Offers**: Professional offer letters with Rand Water branding
- **Payslip Preview**: Mock payslips for employee reference
- **SAP Export Files**: Generate files for bulk SAP upload

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <randwater-repo-url>
cd randwater-calculator

# Install dependencies
pip install -r requirements_randwater.txt

# Set environment variables
export RANDWATER_SAP_URL=https://sap.randwater.co.za
export RANDWATER_SAP_USER=your_username
export RANDWATER_SAP_PASS=your_password
```

### 2. Run the Application

```bash
# Development mode
python randwater_calculator.py

# Production mode
gunicorn -w 4 -b 0.0.0.0:5001 randwater_calculator:app
```

### 3. Access the Calculator

- **Main Calculator**: http://localhost:5001/calculator
- **Admin Panel**: http://localhost:5001/admin/randwater
- **Admin Credentials**: 
  - Username: `RandWaterAdmin`
  - Password: `RandWater2024!`

## Rand Water ESS Portal Integration

### iFrame Embedding

Add this code to your Rand Water ESS portal:

```html
<iframe 
  src="https://calculator.randwater.co.za/calculator?user_id=EMPLOYEE_ID&sso_token=TOKEN" 
  width="100%" 
  height="800px" 
  frameborder="0"
  title="Rand Water Salary Package Calculator">
</iframe>
```

### SSO Integration

```javascript
// In your Rand Water ESS portal
function openRandWaterCalculator(employeeId) {
  const ssoToken = getRandWaterSSOToken();
  const calculatorUrl = `https://calculator.randwater.co.za/calculator?user_id=${employeeId}&sso_token=${ssoToken}`;
  document.getElementById('randwater-calculator-frame').src = calculatorUrl;
}
```

## Rand Water SAP Integration

### Configuration

Create a `.env` file with your Rand Water SAP credentials:

```env
# Rand Water SAP Configuration
RANDWATER_SAP_URL=https://sap.randwater.co.za
RANDWATER_SAP_USER=randwater_sap_user
RANDWATER_SAP_PASS=randwater_sap_password
RANDWATER_SAP_CLIENT=100

# Rand Water ESS Integration
RANDWATER_ESS_VALIDATION_URL=https://ess.randwater.co.za/validate-token
RANDWATER_ESS_API_KEY=randwater_ess_api_key
```

### API Endpoints

- **Get Employee Data**: `GET /api/randwater/employee/<employee_id>`
- **Submit Package**: `POST /api/randwater/package/submit`
- **Export Packages**: `GET /api/randwater/packages/export`
- **Calculate**: `POST /calculate/randwater`

## Rand Water Specific Benefits

The calculator includes Rand Water specific benefits and allowances:

### 💧 **Rand Water Benefits**
- **Water Allowance**: Monthly water-related allowance
- **Infrastructure Bonus**: Bonus for infrastructure projects
- **Environmental Incentive**: Incentive for environmental initiatives
- **Other Rand Water Benefits**: Customizable additional benefits

### 🏢 **Standard Benefits**
- **Travel Allowance**: Transport and travel expenses
- **Cellphone Allowance**: Mobile communication costs
- **Internet Allowance**: Internet connectivity costs
- **Medical Aid**: Healthcare coverage
- **Pension/Provident Fund**: Retirement savings

## File Structure

```
randwater-calculator/
├── randwater_calculator.py          # Main Rand Water application
├── requirements_randwater.txt       # Rand Water specific dependencies
├── templates/
│   ├── randwater_calculator.html    # Main calculator interface
│   ├── randwater_admin_login.html   # Admin login page
│   └── randwater_admin_panel.html   # Admin dashboard
├── static/
│   └── images/
│       └── randwater-logo.png       # Rand Water logo
├── exports/                         # SAP export files
├── logs/                           # Application logs
└── README_RANDWATER.md             # This file
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RANDWATER_SAP_URL` | Rand Water SAP system URL | `https://sap.randwater.co.za` |
| `RANDWATER_SAP_USER` | Rand Water SAP username | `randwater_user` |
| `RANDWATER_SAP_PASS` | Rand Water SAP password | `randwater_pass` |
| `RANDWATER_SAP_CLIENT` | Rand Water SAP client | `100` |
| `RANDWATER_ESS_VALIDATION_URL` | Rand Water ESS validation URL | `https://ess.randwater.co.za/validate-token` |
| `SECRET_KEY` | Flask secret key | `randwater-super-secret-key-2024` |

### Tax Settings

The calculator uses Rand Water specific tax settings stored in `randwater_tax_settings.json`:

```json
{
  "rebate_primary": 17235,
  "rebate_secondary": 9444,
  "rebate_tertiary": 3145,
  "uif_ceiling": 177.12,
  "medical_main": 364,
  "medical_first": 364,
  "medical_additional": 246
}
```

## Deployment

### Production Deployment

1. **Follow the deployment guide**: See `RANDWATER_DEPLOYMENT_GUIDE.md`
2. **Set up reverse proxy**: Configure Nginx for `calculator.randwater.co.za`
3. **SSL certificate**: Install SSL certificate for HTTPS
4. **Environment variables**: Configure production environment variables
5. **Database setup**: Optional database for package storage

### Docker Deployment

```bash
# Build Rand Water calculator image
docker build -t randwater-calculator .

# Run Rand Water calculator
docker run -p 5001:5001 --env-file .env randwater-calculator
```

## Testing

### Unit Tests

```bash
# Run Rand Water specific tests
python -m pytest tests/test_randwater.py
```

### Integration Tests

```bash
# Test Rand Water SAP integration
curl -H "X-SSO-Token: test-token" \
     -H "X-User-ID: RW001" \
     http://localhost:5001/api/randwater/employee/RW001
```

## Admin Panel

### Access Admin Panel

1. Navigate to `/admin/randwater`
2. Login with Rand Water admin credentials
3. Configure tax settings and manage packages

### Admin Features

- **Tax Settings**: Configure SARS tax brackets and rebates
- **Package Management**: View and export completed packages
- **System Statistics**: Monitor package submission rates
- **Recent Activity**: View recent package submissions

## Troubleshooting

### Common Issues

1. **SAP Connection Failed**
   - Check Rand Water SAP credentials
   - Verify network connectivity to SAP system
   - Review SAP endpoint configuration

2. **ESS Integration Issues**
   - Verify CORS settings for Rand Water ESS domain
   - Check SSO token validation
   - Ensure iframe permissions are correct

3. **Calculation Errors**
   - Verify tax settings configuration
   - Check input data validation
   - Review calculation logic

### Logs

Check application logs for detailed error information:

```bash
# View Rand Water calculator logs
tail -f logs/randwater_calculator.log
```

## Support

For Rand Water specific support and configuration:

- **Technical Support**: Contact your IT department
- **SAP Integration**: Contact Rand Water SAP team
- **ESS Integration**: Contact Rand Water ESS team

## License

This calculator is specifically developed for Rand Water and is proprietary software.

---

**Rand Water Salary Package Calculator v1.0**  
*Designed specifically for Rand Water employees and ESS portal integration* 