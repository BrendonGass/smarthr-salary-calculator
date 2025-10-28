# Rand Water Admin Training Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Getting Started](#getting-started)
3. [Core Admin Functions](#core-admin-functions)
4. [Employee Management](#employee-management)
5. [Package Management](#package-management)
6. [Salary Simulator](#salary-simulator)
7. [Export and Reporting](#export-and-reporting)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## System Overview

The Rand Water Package Builder and Salary Simulator is a comprehensive compensation management system designed specifically for Rand Water employees. As an admin, you have access to powerful tools for managing employee packages and creating salary simulations.

### Key Features for Admins:
- **SAP Data Upload**: Import employee data from Excel files
- **Employee Access Management**: Control who can access the Package Builder
- **Package Monitoring**: Track employee package submissions
- **Salary Simulator**: Create dummy payslips for testing scenarios
- **Export Functionality**: Generate files for SAP re-upload
- **Analytics Dashboard**: View comprehensive package statistics

---

## Getting Started

### 1. Accessing the Admin Panel

**URL**: `http://localhost:5001/admin/randwater`

**Default Credentials**:
- Username: `RandWaterAdmin`
- Password: `RandWater2024!`

### 2. Admin Dashboard Overview

The dashboard provides:
- **Statistics Cards**: Active employees, pending submissions, completed packages
- **Feature Cards**: Quick access to main functions
- **Notifications**: Recent system alerts
- **Employee Tables**: Active employees, pending submissions, completed packages

---

## Core Admin Functions

### 1. Upload SAP Data

**Purpose**: Import employee data from SAP Excel files to create employee packages.

**Steps**:
1. Click **"Upload SAP Data"** from the dashboard
2. Prepare your Excel file with required columns:
   - Employee ID
   - First Name
   - Surname
   - Grade Band (O-Q only)
   - Basic Salary (TPE)
   - CTC
   - Department
   - Job Title
   - Car Allowance
   - Cellphone Allowance
   - Housing Allowance
   - Medical Aid Amount
   - Other allowances

3. Click **"Choose File"** and select your Excel file
4. Click **"Upload SAP Data"**
5. System will automatically:
   - Process O-Q band employees only
   - Generate unique login credentials
   - Create employee packages
   - Set 30-day access expiration

**Important Notes**:
- Only O-Q band employees are processed
- Employee access credentials are generated automatically
- Access expires after 30 days
- Previous data is backed up before new upload

### 2. Manage Employee Access

**Purpose**: Monitor and manage employee access to the Package Builder.

**Features**:
- View all active employees
- Check access status and expiration dates
- Monitor package submission status
- View employee login credentials
- Track submission history

**Actions Available**:
- **View Employee Details**: Click "View" to see detailed employee information
- **Check Package Status**: Monitor if packages are submitted or pending
- **Access Credentials**: View username/password for each employee

---

## Employee Management

### 1. Active Employees

**Viewing Active Employees**:
1. Click on the **"Active Employees"** statistics card
2. Or navigate to **"Manage Employee Access"**
3. View the table showing:
   - Employee ID
   - Grade Band
   - Username
   - Access Granted Date
   - Access Expiration Date
   - Status (Active/Inactive)
   - Package Status (Pending/Submitted)

### 2. Employee Details Modal

**Accessing Employee Details**:
1. Click **"View"** next to any employee
2. Modal displays:
   - Basic Information (ID, Username, Grade Band)
   - Access Information (Dates, Login History)
   - Package Details (if created)
   - Login Credentials

### 3. Monitoring Submissions

**Pending Submissions**:
- View employees who haven't submitted packages
- Check days remaining until access expires
- Monitor submission progress

**Submitted Packages**:
- View completed package submissions
- Check TCTC limits vs final TCTC
- Review submission dates
- Export completed packages

---

## Package Management

### 1. Package Analytics

**Purpose**: View comprehensive statistics about employee packages.

**Available Analytics**:
- Package distribution by grade band
- TCTC range analysis
- Submission trends
- Component breakdowns
- Completion rates

### 2. Package Viewing

**Viewing Individual Packages**:
1. Click **"View Packages"** from dashboard
2. Browse all employee packages
3. View detailed package components
4. Check TCTC calculations
5. Review submission status

---

## Salary Simulator

### 1. Accessing the Simulator

**Purpose**: Create dummy payslips and test salary scenarios for offering purposes.

**Access**: Click **"Salary Simulator"** from the admin dashboard

### 2. Simulator Features

**Available Options**:
- **Employee Information**: Name, ID, Grade Band
- **Salary Components**:
  - Basic Salary (TPE)
  - Car Allowance
  - Cellphone Allowance
  - Data Service Allowance
  - Housing Allowance
  - Medical Aid
  - Annual Bonus
  - Other allowances

- **Deductions**:
  - Pension/Provident Fund
  - Medical Aid
  - UIF
  - Tax calculations

### 3. Using the Simulator

**Steps**:
1. Enter employee details
2. Adjust salary components
3. Configure deductions
4. View real-time calculations
5. Generate payslip preview
6. Print or save results

**Calculation Features**:
- SARS-compliant tax calculations
- UIF calculations (1% of basic salary)
- Medical aid tax credits
- Pension fund caps
- Travel allowance rules (80% taxable)

---

## Export and Reporting

### 1. Export Packages for SAP

**Purpose**: Generate Excel files with completed packages for SAP upload.

**Steps**:
1. Click **"Export Packages"** from dashboard
2. System generates Excel file with:
   - Employee details
   - Package components
   - TCTC calculations
   - Submission dates
3. Download the file
4. Upload to SAP system

### 2. Package Reports

**Available Reports**:
- Completed packages summary
- Pending submissions report
- Package analytics report
- Employee access report

---

## Troubleshooting

### Common Issues

#### 1. Upload Errors
**Problem**: Excel file upload fails
**Solutions**:
- Check file format (must be .xlsx)
- Verify required columns are present
- Ensure file size is reasonable
- Check for special characters in data

#### 2. Employee Access Issues
**Problem**: Employee cannot login
**Solutions**:
- Check if access has expired (30-day limit)
- Verify credentials are correct
- Check if package was already submitted
- Reset access if needed

#### 3. Package Submission Problems
**Problem**: Employee cannot submit package
**Solutions**:
- Check if TCTC is within limits
- Verify all required fields are completed
- Check for validation errors
- Ensure access hasn't expired

### Error Messages

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Invalid credentials" | Wrong username/password | Check credentials |
| "Access expired" | 30-day limit reached | Contact admin for renewal |
| "Package already submitted" | Employee already submitted | View submitted package |
| "TCTC limit exceeded" | Package exceeds limits | Adjust package components |

---

## Best Practices

### 1. Data Management
- **Regular Backups**: System creates automatic backups
- **File Validation**: Always validate Excel files before upload
- **Data Cleanup**: Remove old/expired employee data regularly

### 2. Employee Communication
- **Clear Instructions**: Provide employees with clear login instructions
- **Timeline Management**: Set realistic deadlines for package submission
- **Support**: Be available to help employees with technical issues

### 3. Security
- **Access Control**: Monitor who has access to the system
- **Password Management**: Use strong passwords for admin accounts
- **Session Management**: Log out when not using the system

### 4. Workflow Optimization
- **Batch Processing**: Upload multiple employees at once
- **Status Monitoring**: Regularly check submission status
- **Export Scheduling**: Export completed packages regularly

### 5. System Maintenance
- **Regular Updates**: Keep the system updated
- **Performance Monitoring**: Monitor system performance
- **User Feedback**: Collect feedback from employees

---

## Support and Resources

### Getting Help
- **Technical Issues**: Contact IT support
- **System Questions**: Refer to this guide
- **Employee Issues**: Use the admin tools to diagnose problems

### Additional Resources
- **User Manual**: Complete system documentation
- **Video Tutorials**: Step-by-step video guides
- **FAQ**: Frequently asked questions
- **Contact Support**: Technical support contact information

---

## Quick Reference

### Admin URLs
- **Main Dashboard**: `/admin/randwater`
- **Upload SAP Data**: `/admin/randwater/upload-sap-data`
- **Manage Access**: `/admin/randwater/manage-employee-access`
- **Salary Simulator**: `/admin/randwater/salary-simulator`
- **Export Packages**: `/admin/randwater/export-packages`

### Key Statistics
- **Access Duration**: 30 days per employee
- **Grade Bands**: O-Q only
- **Package Components**: 8 main components
- **Tax Compliance**: SARS-compliant calculations

### Important Notes
- Only O-Q band employees can use Package Builder
- Access automatically expires after 30 days
- Packages can only be submitted once
- All calculations are SARS-compliant
- System creates automatic backups

---

*This training guide is designed to help Rand Water administrators effectively use the Package Builder and Salary Simulator system. For additional support or questions, please contact the system administrator.*
