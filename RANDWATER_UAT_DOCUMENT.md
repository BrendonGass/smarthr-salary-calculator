# Rand Water Package Builder - User Acceptance Testing (UAT) Document

## Document Information
- **Project**: Rand Water Package Builder and Salary Simulator
- **Version**: 1.0
- **Date**: October 2025
- **Test Environment**: http://localhost:5001
- **UAT Scope**: Admin and Employee functions (excluding Super Admin)

---

## Table of Contents
1. [Test Overview](#test-overview)
2. [Test Approach](#test-approach)
3. [Test Scenarios - Admin Functions](#test-scenarios---admin-functions)
4. [Test Scenarios - Employee Functions](#test-scenarios---employee-functions)
5. [Test Scenarios - Integration](#test-scenarios---integration)
6. [Test Scenarios - Security](#test-scenarios---security)
7. [Test Scenarios - Performance](#test-scenarios---performance)
8. [Test Data Requirements](#test-data-requirements)
9. [UAT Sign-off](#uat-sign-off)

---

## Test Overview

### Objectives
- Verify all admin functions work correctly
- Validate employee package building workflow
- Ensure security and access control mechanisms
- Test calculation accuracy (SARS compliance)
- Validate data integrity and persistence
- Confirm error handling and user feedback

### Scope
**In Scope**:
- Admin login and dashboard
- SAP data upload functionality
- Employee access management
- Package monitoring and analytics
- Salary simulator
- Export functionality
- Employee login and authentication
- Package builder interface
- Package component adjustments
- Validation rules and warnings
- Package submission
- Tax and net pay calculations

**Out of Scope**:
- Super admin functions
- System configuration
- Database administration
- API testing (covered separately)

### Test Environment
- **URL**: http://localhost:5001
- **Admin Credentials**: RandWaterAdmin / RandWater2024!
- **Employee Test Accounts**: To be created during testing
- **Browser Support**: Chrome, Firefox, Edge

---

## Test Approach

### Testing Methodology
1. **Functional Testing**: Verify all features work as expected
2. **Validation Testing**: Test all validation rules and constraints
3. **Integration Testing**: Test data flow between components
4. **Security Testing**: Verify access controls and authentication
5. **Usability Testing**: Ensure user-friendly interfaces

### Test Execution
- Each test scenario should be executed independently
- Document actual results vs expected results
- Capture screenshots for failures
- Report defects with severity levels

### Defect Severity Levels
- **Critical**: System crash, data loss, security breach
- **High**: Major functionality broken, no workaround
- **Medium**: Feature partially working, workaround exists
- **Low**: Minor issues, cosmetic problems

---

## Test Scenarios - Admin Functions

### TC-A001: Admin Login
**Priority**: Critical  
**Preconditions**: Admin account exists

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-A001-01 | Admin login with valid credentials | 1. Navigate to `/admin/randwater`<br>2. Enter username: RandWaterAdmin<br>3. Enter password: RandWater2024!<br>4. Click Login | Admin dashboard loads successfully | | | |
| TC-A001-02 | Admin login with invalid username | 1. Navigate to `/admin/randwater`<br>2. Enter invalid username<br>3. Enter correct password<br>4. Click Login | Error message: "Invalid credentials" | | | |
| TC-A001-03 | Admin login with invalid password | 1. Navigate to `/admin/randwater`<br>2. Enter correct username<br>3. Enter invalid password<br>4. Click Login | Error message: "Invalid credentials" | | | |
| TC-A001-04 | Admin login with empty fields | 1. Navigate to `/admin/randwater`<br>2. Leave fields empty<br>3. Click Login | Validation error displayed | | | |
| TC-A001-05 | Admin logout | 1. Login as admin<br>2. Click Logout button | Redirected to login page, session cleared | | | |

---

### TC-A002: Admin Dashboard
**Priority**: High  
**Preconditions**: Admin logged in

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-A002-01 | View dashboard statistics | 1. Login as admin<br>2. View dashboard | Statistics cards show: Active Employees, Pending Submissions, Completed Packages | | | |
| TC-A002-02 | View feature cards | 1. Login as admin<br>2. Check feature cards | All 6 feature cards visible: Upload SAP, Manage Access, Salary Simulator, Export Packages, Package Management, Package Analytics | | | |
| TC-A002-03 | View notifications | 1. Login as admin<br>2. Check notifications section | Recent notifications displayed (if any) | | | |
| TC-A002-04 | Navigate to Upload SAP Data | 1. Login as admin<br>2. Click "Upload SAP Data" | Upload page loads | | | |
| TC-A002-05 | Navigate to Manage Access | 1. Login as admin<br>2. Click "Manage Access" | Employee access page loads | | | |
| TC-A002-06 | Navigate to Salary Simulator | 1. Login as admin<br>2. Click "Salary Simulator" | Salary simulator page loads | | | |

---

### TC-A003: SAP Data Upload
**Priority**: Critical  
**Preconditions**: Admin logged in, test Excel file prepared

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-A003-01 | Upload valid SAP Excel file | 1. Navigate to Upload SAP Data<br>2. Select valid Excel file<br>3. Click Upload | Success message, employees processed, credentials generated | | | |
| TC-A003-02 | Upload file with O-Q band employees only | 1. Upload file with 5 O-Q band employees | Only O-Q band employees processed, others ignored | | | |
| TC-A003-03 | Upload file with mixed grade bands | 1. Upload file with O, P, Q, R, S bands | Only O-Q band employees processed | | | |
| TC-A003-04 | Upload file with missing columns | 1. Upload Excel file missing required columns | Error message: "Missing required columns" | | | |
| TC-A003-05 | Upload invalid file format | 1. Select .pdf or .doc file<br>2. Click Upload | Error message: "Invalid file format" | | | |
| TC-A003-06 | Upload empty Excel file | 1. Upload Excel file with no data | Error message: "No valid data found" | | | |
| TC-A003-07 | Upload duplicate employee IDs | 1. Upload file with duplicate employee IDs | Latest data overwrites, warning shown | | | |
| TC-A003-08 | Verify 30-day access creation | 1. Upload valid file<br>2. Check employee access dates | Access granted = today, Expires = today + 30 days | | | |
| TC-A003-09 | Verify credential generation | 1. Upload file<br>2. Check employee credentials | Unique username and password generated for each employee | | | |

---

### TC-A004: Employee Access Management
**Priority**: High  
**Preconditions**: Admin logged in, employees uploaded

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-A004-01 | View active employees list | 1. Navigate to Manage Employee Access<br>2. View employee list | All active employees displayed with details | | | |
| TC-A004-02 | View employee details | 1. Click "View" on an employee<br>2. Check modal | Employee details displayed: ID, credentials, access dates, package status | | | |
| TC-A004-03 | Check employee credentials | 1. View employee details<br>2. Check credentials section | Username and password displayed | | | |
| TC-A004-04 | View employee with pending package | 1. View employee who hasn't submitted | Package status shows "Pending" | | | |
| TC-A004-05 | View employee with submitted package | 1. View employee who submitted<br>2. Check status | Package status shows "Submitted", submission date visible | | | |
| TC-A004-06 | Check access expiration warning | 1. View employee with <5 days remaining | Warning indicator shown | | | |
| TC-A004-07 | Check expired access | 1. View employee past 30 days | Status shows "Expired" or "Inactive" | | | |

---

### TC-A005: Salary Simulator
**Priority**: High  
**Preconditions**: Admin logged in

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-A005-01 | Open salary simulator | 1. Navigate to Salary Simulator | Simulator interface loads with all fields | | | |
| TC-A005-02 | Enter basic salary details | 1. Enter employee details<br>2. Enter basic salary | Fields accept input | | | |
| TC-A005-03 | Calculate with minimum values | 1. Enter minimum valid amounts<br>2. Calculate | Net pay calculated correctly | | | |
| TC-A005-04 | Calculate with maximum values | 1. Enter maximum valid amounts<br>2. Calculate | Net pay calculated correctly | | | |
| TC-A005-05 | Test tax calculation accuracy | 1. Enter known salary amount<br>2. Calculate<br>3. Verify tax amount | Tax matches SARS brackets | | | |
| TC-A005-06 | Test UIF calculation (1%) | 1. Enter basic salary<br>2. Calculate<br>3. Check UIF amount | UIF = 1% of basic salary | | | |
| TC-A005-07 | Test medical aid tax credits | 1. Enter medical aid amount<br>2. Calculate<br>3. Verify tax credits applied | Medical tax credits correctly applied | | | |
| TC-A005-08 | Test car allowance tax (80%) | 1. Enter car allowance<br>2. Calculate<br>3. Verify tax calculation | 80% of car allowance taxable | | | |
| TC-A005-09 | Generate payslip preview | 1. Enter all details<br>2. Generate payslip | Payslip displays all components correctly | | | |
| TC-A005-10 | Print payslip | 1. Generate payslip<br>2. Click Print | Print dialog opens | | | |

---

### TC-A006: Package Management
**Priority**: High  
**Preconditions**: Admin logged in, packages exist

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-A006-01 | View all packages | 1. Navigate to Manage Packages | All employee packages listed | | | |
| TC-A006-02 | View package details | 1. Click View on a package | Package details displayed | | | |
| TC-A006-03 | View pending packages | 1. Filter pending packages | Only pending packages shown | | | |
| TC-A006-04 | View submitted packages | 1. Filter submitted packages | Only submitted packages shown | | | |
| TC-A006-05 | Check TCTC calculations | 1. View package<br>2. Verify TCTC total | TCTC = sum of all components | | | |

---

### TC-A007: Package Analytics
**Priority**: Medium  
**Preconditions**: Admin logged in, packages exist

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-A007-01 | View analytics dashboard | 1. Navigate to Package Analytics | Analytics page loads with statistics | | | |
| TC-A007-02 | View package distribution | 1. Check package distribution by grade | Chart/table shows distribution | | | |
| TC-A007-03 | View TCTC ranges | 1. Check TCTC range analysis | TCTC ranges displayed | | | |
| TC-A007-04 | View submission trends | 1. Check submission statistics | Submission trends shown | | | |

---

### TC-A008: Export Functionality
**Priority**: High  
**Preconditions**: Admin logged in, completed packages exist

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-A008-01 | Export completed packages | 1. Navigate to Export Packages<br>2. Click Export | Excel file downloads with all completed packages | | | |
| TC-A008-02 | Verify export file format | 1. Export packages<br>2. Open file in Excel | File opens correctly with all columns | | | |
| TC-A008-03 | Verify export data accuracy | 1. Export packages<br>2. Compare with system data | All data matches system records | | | |
| TC-A008-04 | Export with no completed packages | 1. Export when no packages submitted | Message: "No packages to export" or empty file | | | |

---

## Test Scenarios - Employee Functions

### TC-E001: Employee Login
**Priority**: Critical  
**Preconditions**: Employee access created by admin

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-E001-01 | Employee login with valid credentials | 1. Navigate to `/employee/login`<br>2. Enter valid username<br>3. Enter valid password<br>4. Click Login | Package Builder interface loads | | | |
| TC-E001-02 | Employee login with invalid username | 1. Enter invalid username<br>2. Enter valid password<br>3. Click Login | Error: "Invalid credentials or access expired" | | | |
| TC-E001-03 | Employee login with invalid password | 1. Enter valid username<br>2. Enter invalid password<br>3. Click Login | Error: "Invalid credentials or access expired" | | | |
| TC-E001-04 | Login with expired access (>30 days) | 1. Login with expired credentials | Error: "Access expired" | | | |
| TC-E001-05 | Login after package submission | 1. Login after submitting package | Error: "Access revoked" or "Package already submitted" | | | |
| TC-E001-06 | Employee logout | 1. Login<br>2. Click Logout | Redirected to login, session cleared | | | |

---

### TC-E002: Package Builder Interface
**Priority**: High  
**Preconditions**: Employee logged in

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-E002-01 | View employee information | 1. Login as employee<br>2. Check employee info section | Employee ID, name, grade band, department, job title displayed | | | |
| TC-E002-02 | View package overview | 1. Check package overview section | TCTC limit, current TCTC, remaining budget, status shown | | | |
| TC-E002-03 | View days remaining | 1. Check access information | Days remaining until expiry displayed | | | |
| TC-E002-04 | View adjustable components | 1. Check components section | Basic Salary, Car Allowance, Annual Bonus editable | | | |
| TC-E002-05 | View fixed components | 1. Check fixed components | Cellphone, Data Service, Housing, Medical Aid visible but not editable | | | |
| TC-E002-06 | View TCTC progress bar | 1. Check progress bar | Visual indicator shows TCTC usage percentage | | | |

---

### TC-E003: Package Component Adjustments
**Priority**: Critical  
**Preconditions**: Employee logged in

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-E003-01 | Adjust basic salary within range | 1. Enter basic salary (50-70% of TCTC)<br>2. Tab/click away | Value accepted, TCTC updates, no warnings | | | |
| TC-E003-02 | Adjust car allowance above minimum | 1. Enter car allowance (>30% of TCTC)<br>2. Tab/click away | Value accepted, TCTC updates, no warnings | | | |
| TC-E003-03 | Adjust annual bonus within range | 1. Enter bonus (10-70% of TCTC)<br>2. Tab/click away | Value accepted, TCTC updates, no warnings | | | |
| TC-E003-04 | Real-time TCTC calculation | 1. Change any component<br>2. Observe TCTC | TCTC updates immediately without page refresh | | | |
| TC-E003-05 | Real-time remaining budget update | 1. Increase component<br>2. Check remaining budget | Remaining budget decreases immediately | | | |
| TC-E003-06 | Multiple component adjustments | 1. Adjust basic salary<br>2. Adjust car allowance<br>3. Adjust bonus | All changes reflected in TCTC | | | |

---

### TC-E004: Validation Rules - Basic Salary
**Priority**: Critical  
**Preconditions**: Employee logged in

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-E004-01 | Basic salary at 50% of TCTC (minimum) | 1. Set basic salary to exactly 50% of TCTC | Value accepted, no warnings | | | |
| TC-E004-02 | Basic salary at 70% of TCTC (maximum) | 1. Set basic salary to exactly 70% of TCTC | Value accepted, no warnings | | | |
| TC-E004-03 | Basic salary below 50% | 1. Set basic salary < 50% of TCTC | Warning: "Basic salary should be between 50-70% of TCTC" | | | |
| TC-E004-04 | Basic salary above 70% | 1. Set basic salary > 70% of TCTC | Warning: "Basic salary should be between 50-70% of TCTC" | | | |
| TC-E004-05 | Basic salary as negative number | 1. Enter negative value | Error or value rejected | | | |
| TC-E004-06 | Basic salary as zero | 1. Enter 0 | Warning or error displayed | | | |
| TC-E004-07 | Basic salary with decimals | 1. Enter value with decimals (e.g., 25000.50) | Value accepted and displayed correctly | | | |

---

### TC-E005: Validation Rules - Car Allowance
**Priority**: Critical  
**Preconditions**: Employee logged in

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-E005-01 | Car allowance at 30% (minimum) | 1. Set car allowance to exactly 30% of TCTC | Value accepted, no warnings | | | |
| TC-E005-02 | Car allowance above 30% | 1. Set car allowance > 30% of TCTC | Value accepted, no warnings | | | |
| TC-E005-03 | Car allowance below 30% | 1. Set car allowance < 30% of TCTC | Warning: "Car allowance must be at least 30% of TCTC" | | | |
| TC-E005-04 | Car allowance as zero | 1. Enter 0 for car allowance | Warning displayed | | | |
| TC-E005-05 | Car allowance as negative | 1. Enter negative value | Error or value rejected | | | |

---

### TC-E006: Validation Rules - Annual Bonus
**Priority**: Critical  
**Preconditions**: Employee logged in

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-E006-01 | Annual bonus at 10% (minimum) | 1. Set bonus to 10% of TCTC | Value accepted, no warnings | | | |
| TC-E006-02 | Annual bonus at 70% (maximum) | 1. Set bonus to 70% of TCTC | Value accepted, no warnings | | | |
| TC-E006-03 | Annual bonus below 10% | 1. Set bonus < 10% of TCTC | Warning: "Annual bonus should be between 10-70% of TCTC" | | | |
| TC-E006-04 | Annual bonus above 70% | 1. Set bonus > 70% of TCTC | Warning: "Annual bonus should be between 10-70% of TCTC" | | | |
| TC-E006-05 | Annual bonus as zero | 1. Enter 0 for bonus | Warning displayed | | | |

---

### TC-E007: TCTC Limit Validation
**Priority**: Critical  
**Preconditions**: Employee logged in

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-E007-01 | Package at TCTC limit | 1. Set components to exactly match TCTC limit | Package valid, no warnings | | | |
| TC-E007-02 | Package below TCTC limit | 1. Set components below TCTC limit | Package valid, remaining budget shown | | | |
| TC-E007-03 | Package exceeds TCTC limit | 1. Increase components to exceed TCTC | Warning: "TCTC exceeds assigned limit" | | | |
| TC-E007-04 | Cannot submit with exceeded TCTC | 1. Exceed TCTC limit<br>2. Try to submit | Submit button disabled or error shown | | | |
| TC-E007-05 | Visual indication of TCTC status | 1. Exceed TCTC<br>2. Check visual indicators | Red warning, progress bar shows >100% | | | |

---

### TC-E008: Package Submission
**Priority**: Critical  
**Preconditions**: Employee logged in, valid package

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-E008-01 | Submit valid package | 1. Create valid package<br>2. Click Submit Package<br>3. Confirm | Success message, access revoked, redirected | | | |
| TC-E008-02 | Submission confirmation dialog | 1. Click Submit<br>2. Check confirmation | Modal/dialog asks for confirmation | | | |
| TC-E008-03 | Cancel submission | 1. Click Submit<br>2. Click Cancel in dialog | Submission cancelled, stays in builder | | | |
| TC-E008-04 | Submit with warnings | 1. Create package with warnings<br>2. Try to submit | Submit blocked or warning displayed | | | |
| TC-E008-05 | Submit with exceeded TCTC | 1. Exceed TCTC<br>2. Try to submit | Submit blocked, error message shown | | | |
| TC-E008-06 | Verify access revocation after submit | 1. Submit package<br>2. Try to login again | Login fails with "Access revoked" message | | | |
| TC-E008-07 | Verify notification sent to admin | 1. Submit package<br>2. Check admin notifications | Admin receives notification of submission | | | |
| TC-E008-08 | View submission confirmation | 1. Submit package<br>2. Check confirmation screen | Employee ID, final TCTC, net pay, submission date shown | | | |

---

### TC-E009: Tax and Net Pay Calculations
**Priority**: Critical  
**Preconditions**: Employee logged in

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-E009-01 | Calculate net pay with minimum package | 1. Set minimum valid package<br>2. View net pay | Net pay calculated correctly | | | |
| TC-E009-02 | Calculate net pay with maximum package | 1. Set maximum valid package<br>2. View net pay | Net pay calculated correctly | | | |
| TC-E009-03 | Verify SARS tax brackets applied | 1. Set specific salary<br>2. Calculate tax<br>3. Verify against SARS tables | Tax matches SARS brackets | | | |
| TC-E009-04 | Verify UIF calculation (1%) | 1. Set basic salary<br>2. Check UIF amount | UIF = 1% of basic salary (capped) | | | |
| TC-E009-05 | Verify medical aid tax credits | 1. Check medical aid component<br>2. Verify tax credits | Medical tax credits applied correctly | | | |
| TC-E009-06 | Verify car allowance tax (80%) | 1. Set car allowance<br>2. Check tax calculation | 80% of car allowance taxable | | | |
| TC-E009-07 | Verify pension deduction cap | 1. Check pension deduction<br>2. Verify cap applied | Pension capped at 27.5% of taxable income | | | |
| TC-E009-08 | Verify bonus tax provision | 1. Set annual bonus<br>2. Check monthly tax provision | Bonus tax provisioned monthly | | | |

---

## Test Scenarios - Integration

### TC-I001: Admin-Employee Workflow
**Priority**: High  
**Preconditions**: None

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-I001-01 | End-to-end workflow | 1. Admin uploads SAP data<br>2. Employee logs in<br>3. Employee adjusts package<br>4. Employee submits<br>5. Admin views submission | Complete workflow succeeds | | | |
| TC-I001-02 | Multiple employees simultaneously | 1. Admin uploads 5 employees<br>2. All 5 login and work concurrently<br>3. All submit | All submissions succeed | | | |
| TC-I001-03 | Data persistence across sessions | 1. Employee adjusts package<br>2. Logout<br>3. Login again | Changes are saved and displayed | | | |

---

### TC-I002: Data Flow and Persistence
**Priority**: High  
**Preconditions**: System operational

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-I002-01 | Package data persists after browser close | 1. Employee adjusts package<br>2. Close browser<br>3. Reopen and login | Package changes retained | | | |
| TC-I002-02 | Submitted packages appear in admin view | 1. Employee submits package<br>2. Admin views submitted packages | Submitted package appears immediately | | | |
| TC-I002-03 | Export reflects latest submissions | 1. Employee submits<br>2. Admin exports immediately | Latest submission included in export | | | |

---

## Test Scenarios - Security

### TC-S001: Authentication and Authorization
**Priority**: Critical  
**Preconditions**: None

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-S001-01 | Admin cannot access employee routes | 1. Login as admin<br>2. Navigate to `/employee/package-builder` | Access denied or redirected | | | |
| TC-S001-02 | Employee cannot access admin routes | 1. Login as employee<br>2. Navigate to `/admin/randwater` | Access denied or redirected | | | |
| TC-S001-03 | Unauthenticated access blocked | 1. Without login, access protected pages | Redirected to login | | | |
| TC-S001-04 | Session timeout | 1. Login<br>2. Wait for timeout period<br>3. Try to use system | Session expired, must re-login | | | |
| TC-S001-05 | Concurrent session handling | 1. Login on browser 1<br>2. Login same user on browser 2<br>3. Use both | Appropriate session handling | | | |

---

### TC-S002: Access Control
**Priority**: Critical  
**Preconditions**: Employees with various statuses

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-S002-01 | Expired access blocked | 1. Try to login with expired (>30 days) credentials | Access denied with appropriate message | | | |
| TC-S002-02 | Revoked access blocked | 1. Try to login with revoked credentials (after submission) | Access denied with appropriate message | | | |
| TC-S002-03 | Active access allowed | 1. Login with active credentials (<30 days, not submitted) | Access granted | | | |

---

### TC-S003: Data Security
**Priority**: High  
**Preconditions**: Multiple employees exist

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-S003-01 | Employee can only view own package | 1. Login as Employee A<br>2. Try to access Employee B's package | Access denied or only own package shown | | | |
| TC-S003-02 | Password not displayed in plain text | 1. Check all pages<br>2. Check browser DevTools | Password fields use type="password" | | | |
| TC-S003-03 | SQL injection prevention | 1. Enter SQL commands in input fields<br>2. Submit | SQL commands treated as text, not executed | | | |
| TC-S003-04 | XSS prevention | 1. Enter JavaScript in fields<br>2. Submit | Script not executed, treated as text | | | |

---

## Test Scenarios - Performance

### TC-P001: System Performance
**Priority**: Medium  
**Preconditions**: Test data loaded

| Test Case ID | Test Description | Test Steps | Expected Result | Actual Result | Status | Comments |
|--------------|-----------------|------------|-----------------|---------------|---------|----------|
| TC-P001-01 | Admin dashboard load time | 1. Login as admin<br>2. Measure dashboard load time | Dashboard loads in <3 seconds | | | |
| TC-P001-02 | Employee package builder load | 1. Login as employee<br>2. Measure page load time | Page loads in <3 seconds | | | |
| TC-P001-03 | Real-time calculation speed | 1. Adjust package component<br>2. Measure calculation time | Calculation completes in <1 second | | | |
| TC-P001-04 | SAP upload with large file | 1. Upload file with 100 employees<br>2. Measure processing time | Processing completes in reasonable time | | | |
| TC-P001-05 | Export large dataset | 1. Export 100 completed packages<br>2. Measure export time | Export completes in reasonable time | | | |

---

## Test Data Requirements

### Admin Test Data
```
Admin Account:
Username: RandWaterAdmin
Password: RandWater2024!
```

### Employee Test Data (Sample Excel File)

| Employee ID | First Name | Surname | Grade Band | Basic Salary | CTC | Department | Job Title | Car Allowance | Cellphone | Housing | Medical Aid |
|------------|-----------|---------|------------|--------------|-----|------------|-----------|---------------|-----------|---------|-------------|
| RW001 | John | Smith | O | 25000 | 45000 | Finance | Analyst | 15000 | 500 | 2000 | 1200 |
| RW002 | Jane | Doe | P | 30000 | 55000 | HR | Manager | 18000 | 500 | 2500 | 1500 |
| RW003 | Bob | Wilson | Q | 35000 | 65000 | IT | Senior Manager | 22000 | 500 | 3000 | 1800 |
| RW004 | Alice | Brown | R | 40000 | 75000 | Operations | Director | 25000 | 500 | 3500 | 2000 |
| RW005 | Charlie | Davis | S | 45000 | 85000 | Sales | Executive | 28000 | 500 | 4000 | 2200 |

**Note**: Only RW001, RW002, RW003 (O-Q bands) should be processed

### Test Scenarios Data

| Scenario | Employee ID | Grade | TCTC Limit | Initial Basic | Initial Car | Initial Bonus | Expected Outcome |
|----------|-------------|-------|------------|---------------|-------------|---------------|------------------|
| Valid Package | TEST001 | O | 45000 | 28000 (62%) | 13500 (30%) | 2500 (5.6%) | Success |
| Basic Too Low | TEST002 | P | 55000 | 20000 (36%) | 25000 | 5000 | Warning: Basic salary below 50% |
| Car Too Low | TEST003 | Q | 65000 | 40000 | 15000 (23%) | 5000 | Warning: Car allowance below 30% |
| TCTC Exceeded | TEST004 | O | 45000 | 35000 | 20000 | 5000 | Error: TCTC exceeded |

---

## UAT Sign-off

### Test Summary
| Metric | Value |
|--------|-------|
| Total Test Cases | [To be filled] |
| Passed | [To be filled] |
| Failed | [To be filled] |
| Blocked | [To be filled] |
| Not Executed | [To be filled] |
| Pass Rate | [To be calculated] |

### Critical Issues
| Issue ID | Description | Severity | Status |
|----------|-------------|----------|--------|
| | | | |

### Sign-off Criteria
- [ ] All critical test cases passed
- [ ] All high priority test cases passed
- [ ] No critical or high severity defects open
- [ ] All medium severity defects documented and accepted
- [ ] Performance requirements met
- [ ] Security requirements met
- [ ] User documentation reviewed and approved

### Approvals

**Business Owner**  
Name: ___________________________  
Signature: ___________________________  
Date: ___________________________

**Project Manager**  
Name: ___________________________  
Signature: ___________________________  
Date: ___________________________

**QA Lead**  
Name: ___________________________  
Signature: ___________________________  
Date: ___________________________

**IT Manager**  
Name: ___________________________  
Signature: ___________________________  
Date: ___________________________

---

## Appendix

### Test Execution Schedule
- Week 1: Admin Functions (TC-A001 to TC-A008)
- Week 2: Employee Functions (TC-E001 to TC-E009)
- Week 3: Integration and Security (TC-I001 to TC-S003)
- Week 4: Performance and Regression (TC-P001 + Regression)

### Defect Reporting Template
```
Defect ID: [Auto-generated]
Test Case ID: [Reference]
Summary: [Brief description]
Description: [Detailed description]
Steps to Reproduce: [Numbered steps]
Expected Result: [What should happen]
Actual Result: [What actually happened]
Severity: [Critical/High/Medium/Low]
Screenshot: [Attached]
Environment: [Browser, OS]
Reported By: [Name]
Date: [Date]
```

### Browser Compatibility Matrix
| Browser | Version | Supported | Tested |
|---------|---------|-----------|--------|
| Chrome | Latest | Yes | [ ] |
| Firefox | Latest | Yes | [ ] |
| Edge | Latest | Yes | [ ] |
| Safari | Latest | No | [ ] |

---

*End of UAT Document*

