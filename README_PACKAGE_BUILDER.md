# Rand Water Package Builder & Salary Simulator

## Overview

The Rand Water Package Builder and Salary Simulator is a comprehensive compensation management system designed specifically for Rand Water employees. It consists of two main components:

1. **Package Builder (TCTC Modeler)** - Employee portal for O-Q band employees to model their compensation packages
2. **Salary Simulator (Net Pay Modeler)** - Administrative tool for creating dummy payslips and testing salary scenarios

## Features

### 🏗️ Package Builder (TCTC Modeler)

#### For Employees (O-Q Band)
- **Secure Login**: Username/password authentication with time-limited access
- **Package Modeling**: Interactive interface to adjust compensation components
- **Real-time Calculations**: Live TCTC updates as components are modified
- **SARS Compliance**: Accurate tax calculations using current SARS brackets
- **Validation Rules**: Built-in warnings for package component limits
- **Package Submission**: Final submission with automatic access revocation

#### For Administrators
- **SAP Data Upload**: Excel file upload to create employee packages
- **Employee Access Management**: Monitor and manage employee portal access
- **Submission Tracking**: Real-time notifications of package completions
- **Export Functionality**: Generate Excel files for SAP re-upload
- **Dashboard Analytics**: Comprehensive overview of package status

### 🧮 Salary Simulator (Net Pay Modeler)

#### Administrative Features
- **Dummy Payslip Creation**: Test various salary scenarios
- **Flexible Configuration**: All Rand Water specific fields and options
- **Real-time Calculations**: Instant net pay calculations
- **Medical Aid Options**: Support for Rand Water and Bonita's providers
- **Dependant Management**: Subsidised and unsubsidised member calculations
- **Retirement Fund Options**: All Rand Water fund choices

## System Architecture

### Data Models

#### EmployeeAccess
- Manages employee portal access credentials
- Handles access expiration and revocation
- Tracks login history and submission status

#### PackageManager
- Stores employee package data from SAP uploads
- Manages package updates and submissions
- Handles TCTC calculations and validations
- Exports completed packages for SAP

#### NotificationManager
- Tracks package submission notifications
- Manages admin alerts and employee messages
- Provides real-time status updates

### File Storage
- **JSON-based storage** for simplicity and portability
- **Excel file processing** for SAP data import/export
- **Automatic backups** through version control

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager
- Modern web browser

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SmartOffer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements_enhanced_randwater.txt
   ```

3. **Run the application**
   ```bash
   python randwater_package_builder.py
   ```

4. **Access the system**
   - **Admin Portal**: http://localhost:5001/admin/randwater
   - **Employee Portal**: http://localhost:5001/employee/login
   - **Salary Simulator**: http://localhost:5001/admin/salary-simulator

### Default Credentials
- **Admin Username**: `RandWaterAdmin`
- **Admin Password**: `RandWater2024!`

## Usage Guide

### For Administrators

#### 1. Upload SAP Data
1. Navigate to **Upload SAP Data** from the admin dashboard
2. Prepare Excel file with required columns (see sample format below)
3. Upload file - system automatically processes O-Q band employees
4. Employee access credentials are generated automatically

#### 2. Monitor Package Submissions
1. View **Active Employees** table for current access status
2. Check **Pending Submissions** for incomplete packages
3. Review **Submitted Packages** for completed submissions
4. Export completed packages for SAP upload

#### 3. Use Salary Simulator
1. Access **Salary Simulator** from admin dashboard
2. Configure employee subgroup and band range
3. Set salary components and benefits
4. Calculate net pay with real-time results

### For Employees

#### 1. Access Package Builder
1. Login with provided credentials (Employee ID as username)
2. View current package from SAP data
3. Modify editable components within TCTC limits
4. Calculate net pay for different scenarios

#### 2. Package Modeling
1. **Editable Fields**:
   - Basic Salary
   - Provident Fund
   - Car Allowance
   - Annual Bonus
2. **Read-only Fields** (SAP data):
   - Cellphone Allowance
   - Data Service Allowance
   - Housing Allowance
   - Medical Aid

#### 3. Submit Package
1. Review final package configuration
2. Click **Submit Package** button
3. Access is automatically revoked
4. Admin receives notification

## SAP Data Format

### Required Excel Columns
| Column | Description | Type | Required |
|--------|-------------|------|----------|
| Employee ID | Unique employee identifier | Text | Yes |
| Grade Band | Employee grade (O, P, Q) | Text | Yes |
| Basic Salary | Monthly basic salary | Number | Yes |
| TCTC Limit | Total cost to company limit | Number | Yes |
| Provident Fund | Retirement fund contribution | Number | No |
| Car Allowance | Vehicle allowance amount | Number | No |
| Cellphone Allowance | Mobile phone allowance | Number | No |
| Data Service Allowance | Internet/data allowance | Number | No |
| Housing Allowance | Housing subsidy amount | Number | No |
| Medical Aid | Medical aid contribution | Number | No |
| Medical Aid Option | Medical aid plan option | Text | No |
| Bonus | Annual bonus amount | Number | No |

### Sample Data
```
Employee ID | Grade Band | Basic Salary | TCTC Limit | Provident Fund | Car Allowance
RW001      | O          | 25000.00     | 35000.00   | 1750.00        | 5000.00
RW002      | P          | 30000.00     | 42000.00   | 2100.00        | 6000.00
```

## Validation Rules

### Package Component Limits (O-Q Band Employees)

#### Total Pensionable Emolument
- **Range**: 50% - 70% of TCTC
- **Warning**: Displayed if outside range
- **Action**: Employee can adjust within limits

#### Car Allowance
- **Minimum**: 30% of TCTC
- **Warning**: Displayed if below minimum
- **Action**: Employee can increase amount

#### Annual Bonus (13th Cheque)
- **Range**: 10% - 70% of TCTC
- **Warning**: Displayed if outside range
- **Action**: Employee can adjust within limits

#### Fixed Components (Cannot be changed)
- Cellphone Allowance
- Data Service Allowance
- Housing Allowance
- Medical Aid (amount and option)

## Security Features

### Employee Access Control
- **Time-limited access**: 30 days from creation
- **Automatic revocation**: After package submission
- **Unique credentials**: Generated per employee
- **Session management**: Secure logout handling

### Admin Security
- **Admin-only routes**: Protected access to sensitive functions
- **File validation**: Excel file type and content validation
- **Data sanitization**: Input validation and sanitization
- **Audit trail**: All actions logged and tracked

## API Endpoints

### Employee Endpoints
- `POST /api/employee/package/update` - Update package components
- `POST /api/employee/package/submit` - Submit completed package
- `POST /api/employee/calculate-net-pay` - Calculate net pay

### Admin Endpoints
- `POST /api/salary-simulator/calculate` - Calculate salary simulation
- `GET /admin/randwater/export-packages` - Export completed packages

## Configuration

### Environment Variables
```bash
# Rand Water SAP Configuration
RANDWATER_SAP_URL=https://sap.randwater.co.za
RANDWATER_SAP_USER=randwater_sap_user
RANDWATER_SAP_PASS=randwater_sap_password
RANDWATER_SAP_CLIENT=100

# Application Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

### Tax Settings
Tax settings are stored in `randwater_tax_settings.json`:
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
1. **Set environment variables** for production
2. **Use production WSGI server** (Gunicorn, uWSGI)
3. **Configure reverse proxy** (Nginx, Apache)
4. **Enable HTTPS** with SSL certificates
5. **Set up monitoring** and logging

### Docker Deployment
```bash
# Build image
docker build -t randwater-package-builder .

# Run container
docker run -p 5001:5001 --env-file .env randwater-package-builder
```

## Troubleshooting

### Common Issues

#### SAP Upload Errors
- **File format**: Ensure Excel (.xlsx) format
- **Column names**: Match exact column headers
- **Data types**: All monetary values must be numeric
- **Grade bands**: Only O, P, Q employees are processed

#### Employee Access Issues
- **Credentials**: Verify username/password combination
- **Access expired**: Check if 30-day period has passed
- **Package submitted**: Access revoked after submission

#### Calculation Errors
- **Tax settings**: Verify tax configuration file
- **Input validation**: Check for invalid numeric values
- **Dependencies**: Ensure all required packages are installed

### Logs
- **Application logs**: Check console output for errors
- **File logs**: Review generated log files
- **Browser console**: Check for JavaScript errors

## Support & Maintenance

### Regular Maintenance
- **Data backups**: Regular backup of JSON data files
- **Log rotation**: Manage log file sizes
- **Security updates**: Keep dependencies updated
- **Performance monitoring**: Monitor system response times

### Support Contacts
- **Technical Issues**: IT Department
- **SAP Integration**: SAP Team
- **Business Rules**: HR Department
- **User Training**: Training Team

## Future Enhancements

### Planned Features
- **Database integration**: Replace JSON files with proper database
- **Advanced analytics**: Detailed reporting and insights
- **Mobile optimization**: Responsive design for mobile devices
- **API integration**: RESTful API for external systems
- **Multi-language support**: Localization for different regions

### Scalability Improvements
- **Caching**: Redis integration for performance
- **Load balancing**: Multiple server instances
- **Microservices**: Break down into smaller services
- **Cloud deployment**: AWS/Azure integration

## License

This system is proprietary software developed specifically for Rand Water. All rights reserved.

---

**Rand Water Package Builder & Salary Simulator v1.0**  
*Comprehensive compensation management for Rand Water employees*
