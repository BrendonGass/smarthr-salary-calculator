# Rand Water Employee Training Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Getting Started](#getting-started)
3. [Package Builder Interface](#package-builder-interface)
4. [Understanding Your Package](#understanding-your-package)
5. [Adjusting Package Components](#adjusting-package-components)
6. [Validation and Warnings](#validation-and-warnings)
7. [Submitting Your Package](#submitting-your-package)
8. [Understanding Calculations](#understanding-calculations)
9. [Troubleshooting](#troubleshooting)
10. [Frequently Asked Questions](#frequently-asked-questions)

---

## System Overview

The Rand Water Package Builder is a secure, user-friendly tool designed specifically for O-Q band employees to model and customize their compensation packages. This system allows you to adjust various components of your package while staying within Rand Water's guidelines and SARS tax regulations.

### Key Features for Employees:
- **Secure Access**: Time-limited login with unique credentials
- **Real-time Calculations**: Live updates as you adjust components
- **SARS Compliance**: Accurate tax calculations
- **Validation Rules**: Built-in warnings for package limits
- **One-time Submission**: Submit your final package choice

### Important Notes:
- **Access Duration**: You have 30 days to complete your package
- **One Submission**: You can only submit your package once
- **Grade Band**: Only available for O-Q band employees
- **Secure Process**: Your access is automatically revoked after submission

---

## Getting Started

### 1. Receiving Your Access Credentials

Your HR administrator will provide you with:
- **Username**: Unique login username
- **Password**: Secure password
- **Access Period**: 30 days from creation
- **Instructions**: How to access the system

### 2. Accessing the Package Builder

**URL**: `http://localhost:5001/employee/login`

**Login Steps**:
1. Open your web browser
2. Navigate to the login URL
3. Enter your username and password
4. Click **"Login"**
5. You'll be redirected to the Package Builder

### 3. First Time Login

When you first log in, you'll see:
- **Welcome Message**: Confirmation of successful login
- **Your Information**: Employee details and current package
- **Package Components**: Current salary breakdown
- **TCTC Limit**: Your maximum package value
- **Access Information**: Days remaining to complete

---

## Package Builder Interface

### 1. Header Section

**Company Branding**:
- Rand Water logo and colors
- System title and tagline
- Your employee information display

**User Information Panel**:
- Employee ID
- Name
- Grade Band
- Department
- Job Title
- Days remaining for access

### 2. Package Overview Section

**Current Package Summary**:
- **TCTC Limit**: Your maximum package value
- **Current TCTC**: Total of all components
- **Remaining Budget**: Available amount to allocate
- **Package Status**: Pending/Submitted

**Visual Indicators**:
- Progress bar showing TCTC usage
- Color-coded status indicators
- Warning messages for limits

### 3. Package Components Section

**Adjustable Components**:
- **Basic Salary (TPE)**: Your base salary
- **Car Allowance**: Vehicle allowance
- **Annual Bonus**: 13th cheque amount

**Fixed Components** (Cannot be changed):
- **Cellphone Allowance**: Fixed amount
- **Data Service Allowance**: Fixed amount
- **Housing Allowance**: Fixed amount
- **Medical Aid**: Fixed amount and option

---

## Understanding Your Package

### 1. Package Components Explained

#### Basic Salary (TPE)
- **What it is**: Your monthly base salary
- **Range**: 50% - 70% of your TCTC
- **Tax Treatment**: Fully taxable
- **UIF**: 1% deduction for UIF

#### Car Allowance
- **What it is**: Monthly allowance for vehicle expenses
- **Minimum**: 30% of your TCTC
- **Tax Treatment**: 80% taxable (travel allowance rules)
- **Purpose**: Covers vehicle-related costs

#### Annual Bonus (13th Cheque)
- **What it is**: Annual bonus payment
- **Range**: 10% - 70% of your TCTC
- **Payment**: Paid annually, not monthly
- **Tax Treatment**: Tax provisioned monthly

#### Fixed Components
These cannot be changed and are set by Rand Water policy:
- **Cellphone Allowance**: Fixed monthly amount
- **Data Service Allowance**: Fixed monthly amount
- **Housing Allowance**: Fixed monthly amount
- **Medical Aid**: Fixed amount and provider option

### 2. TCTC (Total Cost to Company)

**Definition**: The total value of your compensation package including all benefits and allowances.

**Calculation**:
```
TCTC = Basic Salary + Car Allowance + Cellphone Allowance + 
       Data Service Allowance + Housing Allowance + Medical Aid + 
       Annual Bonus
```

**Important**: Your TCTC cannot exceed your assigned limit.

---

## Adjusting Package Components

### 1. Basic Salary Adjustment

**Steps**:
1. Locate the **Basic Salary (TPE)** field
2. Click on the input field
3. Enter your desired amount
4. System will automatically:
   - Update TCTC calculation
   - Check against limits
   - Display warnings if needed
   - Update remaining budget

**Validation Rules**:
- Must be between 50% - 70% of TCTC
- Cannot exceed remaining budget
- Must be a positive number

### 2. Car Allowance Adjustment

**Steps**:
1. Locate the **Car Allowance** field
2. Enter your desired amount
3. System validates against minimum requirement
4. Updates calculations automatically

**Validation Rules**:
- Must be at least 30% of TCTC
- Cannot exceed remaining budget
- Must be a positive number

### 3. Annual Bonus Adjustment

**Steps**:
1. Locate the **Annual Bonus** field
2. Enter your desired amount
3. System calculates monthly provision
4. Updates TCTC and tax calculations

**Validation Rules**:
- Must be between 10% - 70% of TCTC
- Cannot exceed remaining budget
- Must be a positive number

### 4. Real-time Updates

**Automatic Calculations**:
- TCTC updates as you type
- Remaining budget recalculates
- Tax calculations update
- Validation warnings appear/disappear

**Visual Feedback**:
- Green indicators for valid amounts
- Red warnings for invalid amounts
- Progress bars show usage
- Color-coded status indicators

---

## Validation and Warnings

### 1. Validation Rules

#### Basic Salary Validation
- **Range Check**: 50% - 70% of TCTC
- **Warning**: "Basic salary should be between 50% - 70% of TCTC"
- **Action**: Adjust amount within range

#### Car Allowance Validation
- **Minimum Check**: At least 30% of TCTC
- **Warning**: "Car allowance must be at least 30% of TCTC"
- **Action**: Increase car allowance amount

#### Annual Bonus Validation
- **Range Check**: 10% - 70% of TCTC
- **Warning**: "Annual bonus should be between 10% - 70% of TCTC"
- **Action**: Adjust amount within range

#### TCTC Limit Validation
- **Limit Check**: Cannot exceed assigned TCTC limit
- **Warning**: "TCTC exceeds assigned limit"
- **Action**: Reduce component amounts

### 2. Warning Messages

**Types of Warnings**:
- **Red Warnings**: Critical issues that must be fixed
- **Yellow Warnings**: Recommendations for optimization
- **Blue Information**: Helpful tips and explanations

**Common Warning Messages**:
- "Basic salary is below recommended range"
- "Car allowance is below minimum requirement"
- "TCTC limit exceeded - reduce components"
- "Package optimization suggestions available"

### 3. Resolving Warnings

**Step-by-step Process**:
1. **Read the warning message** carefully
2. **Understand the requirement** (minimum, maximum, range)
3. **Adjust the component** accordingly
4. **Check if warning disappears**
5. **Verify TCTC is within limits**
6. **Ensure all components are valid**

---

## Submitting Your Package

### 1. Pre-submission Checklist

**Before submitting, verify**:
- [ ] All components are within valid ranges
- [ ] TCTC is within your assigned limit
- [ ] No critical warnings are displayed
- [ ] You're satisfied with your package choice
- [ ] You understand this is a one-time submission

### 2. Submission Process

**Steps**:
1. **Review your package** one final time
2. **Click "Submit Package"** button
3. **Confirm submission** in the popup dialog
4. **Wait for confirmation** message
5. **Note**: Your access will be automatically revoked

### 3. Post-submission

**What happens after submission**:
- **Access Revoked**: You can no longer access the system
- **Package Locked**: Your package cannot be changed
- **Notification Sent**: Admin receives notification
- **Export Ready**: Package is ready for SAP upload

**Confirmation Message**:
```
"Package submitted successfully! Your access has been revoked. 
Your package will be processed and uploaded to SAP. 
Thank you for using the Rand Water Package Builder."
```

---

## Understanding Calculations

### 1. Tax Calculations

**SARS Compliance**:
- **Tax Brackets**: Current SARS tax brackets applied
- **Medical Credits**: Medical aid tax credits applied
- **Pension Caps**: Pension fund contribution caps
- **Travel Allowance**: 80% of car allowance taxable
- **UIF**: 1% of basic salary

**Monthly Tax Provision**:
- Tax calculated on monthly income
- Bonus tax provisioned monthly
- Medical aid credits applied
- Age rebates included

### 2. Net Pay Calculation

**Formula**:
```
Net Pay = Total Earnings - Total Deductions

Total Earnings = Basic Salary + Car Allowance + 
                 Cellphone Allowance + Data Service Allowance + 
                 Housing Allowance + Other Allowances

Total Deductions = Pension + Medical Aid + UIF + Tax + 
                   Bonus Tax Provision
```

### 3. Package Breakdown

**Monthly vs Annual**:
- **Monthly Components**: Basic salary, allowances
- **Annual Components**: Bonus (provisioned monthly)
- **Tax Provision**: Bonus tax provisioned monthly
- **Net Pay**: Actual monthly take-home pay

---

## Troubleshooting

### Common Issues

#### 1. Login Problems
**Problem**: Cannot log in
**Solutions**:
- Check username and password carefully
- Ensure caps lock is off
- Check if access has expired (30 days)
- Contact HR if credentials don't work

#### 2. Package Adjustment Issues
**Problem**: Cannot adjust package components
**Solutions**:
- Check if package was already submitted
- Verify you're within the 30-day access period
- Ensure you're using a supported browser
- Refresh the page and try again

#### 3. Calculation Errors
**Problem**: Calculations seem incorrect
**Solutions**:
- Check if all components are within valid ranges
- Verify TCTC is within your limit
- Ensure no warnings are displayed
- Contact HR if calculations seem wrong

#### 4. Submission Problems
**Problem**: Cannot submit package
**Solutions**:
- Resolve all warning messages
- Ensure TCTC is within limits
- Check if package was already submitted
- Verify all required fields are completed

### Error Messages

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Invalid credentials" | Wrong username/password | Check credentials |
| "Access expired" | 30-day limit reached | Contact HR for renewal |
| "Package already submitted" | Already submitted | Contact HR |
| "TCTC limit exceeded" | Package too high | Reduce components |
| "Component out of range" | Invalid amount | Adjust to valid range |

---

## Frequently Asked Questions

### Q1: How long do I have to complete my package?
**A**: You have 30 days from when your access was created to complete and submit your package.

### Q2: Can I change my package after submission?
**A**: No, once submitted, your package cannot be changed. This is a one-time submission.

### Q3: What happens if I don't submit within 30 days?
**A**: Your access will expire and you'll need to contact HR to request renewal.

### Q4: Why can't I change some components?
**A**: Some components (cellphone, data service, housing, medical aid) are fixed by Rand Water policy and cannot be changed.

### Q5: How is my net pay calculated?
**A**: Net pay is calculated using SARS-compliant tax rules, including UIF, medical credits, and travel allowance rules.

### Q6: What if I make a mistake?
**A**: You can adjust components as many times as needed before submission. After submission, contact HR.

### Q7: Is my data secure?
**A**: Yes, the system uses secure login and your access is automatically revoked after submission.

### Q8: Can I access the system from home?
**A**: Yes, as long as you have internet access and your credentials haven't expired.

### Q9: What if I have technical problems?
**A**: Contact HR or IT support for technical assistance.

### Q10: How do I know if my package is valid?
**A**: The system will show warnings for any issues. All warnings must be resolved before submission.

---

## Quick Reference

### Important Numbers
- **Access Duration**: 30 days
- **Basic Salary Range**: 50% - 70% of TCTC
- **Car Allowance Minimum**: 30% of TCTC
- **Annual Bonus Range**: 10% - 70% of TCTC
- **UIF Rate**: 1% of basic salary
- **Travel Allowance Tax**: 80% taxable

### Key URLs
- **Login**: `/employee/login`
- **Package Builder**: `/employee/package-builder`
- **Logout**: `/employee/logout`

### Important Notes
- Only O-Q band employees can use this system
- Access expires after 30 days
- Package submission is one-time only
- All calculations are SARS-compliant
- Fixed components cannot be changed

---

## Support and Contact

### Getting Help
- **HR Department**: For access issues and policy questions
- **IT Support**: For technical problems
- **System Administrator**: For system-related issues

### Contact Information
- **HR Email**: hr@randwater.co.za
- **IT Support**: it-support@randwater.co.za
- **Phone**: Internal extension numbers

---

*This training guide is designed to help Rand Water employees effectively use the Package Builder system. For additional support or questions, please contact your HR department.*

**Remember**: Take your time to understand your package options and make informed decisions. Once submitted, your package cannot be changed, so ensure you're completely satisfied before clicking submit.
