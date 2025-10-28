# Rand Water UAT - Screenshot Capture Guide

## Overview
This guide provides detailed instructions on what screenshots to capture during UAT testing to document test results and create evidence of successful testing.

---

## Screenshot Capture Instructions

### General Guidelines
1. **Resolution**: Capture at 1920x1080 or higher
2. **Format**: PNG or JPEG
3. **Naming Convention**: `TC-[ID]_[Description]_[Status].png`
   - Example: `TC-A001-01_Admin_Login_Success_PASS.png`
4. **Annotations**: Use red boxes/arrows to highlight important areas
5. **Sensitive Data**: Blur/redact sensitive information
6. **Browser Info**: Include browser address bar in screenshots

---

## Admin Function Screenshots

### TC-A001: Admin Login

#### Screenshot 1: Admin Login Page (Before Login)
**Filename**: `TC-A001-01_Admin_Login_Page.png`
**Location**: `/admin/randwater`
**Capture**:
- Full login page showing Rand Water logo
- Username and password fields (empty)
- Login button
- "Powered by GoSmartHR" branding
- Browser address bar

#### Screenshot 2: Admin Login - Invalid Credentials
**Filename**: `TC-A001-02_Admin_Login_Invalid_Credentials.png`
**Location**: `/admin/randwater`
**Capture**:
- Login page with error message displayed
- Red error message: "Invalid credentials"
- Username field with invalid username
- Password field (masked)

#### Screenshot 3: Admin Dashboard After Successful Login
**Filename**: `TC-A001-01_Admin_Dashboard_Success.png`
**Location**: `/admin/randwater/dashboard`
**Capture**:
- Complete dashboard with all sections visible
- Statistics cards (Active Employees, Pending, Completed)
- All 6 feature cards
- Notifications section
- Logout button visible
- Username/session info if displayed

---

### TC-A002: Admin Dashboard

#### Screenshot 4: Dashboard Statistics Cards
**Filename**: `TC-A002-01_Dashboard_Statistics.png`
**Capture**:
- Close-up of three statistics cards
- Numbers clearly visible
- Card labels clearly visible
- Hover effects if applicable

#### Screenshot 5: Feature Cards Section
**Filename**: `TC-A002-02_Feature_Cards.png`
**Capture**:
- All 6 feature cards:
  - Upload SAP Data
  - Manage Employee Access
  - Salary Simulator
  - Export Packages
  - Package Management
  - Package Analytics
- Icons clearly visible
- Buttons clearly visible

#### Screenshot 6: Notifications Section
**Filename**: `TC-A002-03_Notifications.png`
**Capture**:
- Notifications area
- Recent notifications listed (if any)
- Timestamps visible
- Notification types visible

---

### TC-A003: SAP Data Upload

#### Screenshot 7: Upload SAP Data Page
**Filename**: `TC-A003-01_Upload_SAP_Page.png`
**Location**: `/admin/randwater/upload-sap-data`
**Capture**:
- File selection area
- Upload button
- Required columns list
- Important notes section
- Sample format information

#### Screenshot 8: File Selected Before Upload
**Filename**: `TC-A003-02_File_Selected.png`
**Capture**:
- File input showing selected filename
- Upload button ready to click
- File details (name, size if visible)

#### Screenshot 9: Upload Processing
**Filename**: `TC-A003-03_Upload_Processing.png`
**Capture**:
- Processing indicator/spinner
- Progress message
- Loading state

#### Screenshot 10: Upload Success
**Filename**: `TC-A003-01_Upload_Success.png`
**Capture**:
- Success message
- Number of employees processed
- Summary of upload
- Any warnings or notifications

#### Screenshot 11: Upload Error - Invalid File
**Filename**: `TC-A003-05_Upload_Invalid_File.png`
**Capture**:
- Error message displayed
- File type restriction notice
- Failed upload indication

#### Screenshot 12: Upload Error - Missing Columns
**Filename**: `TC-A003-04_Upload_Missing_Columns.png`
**Capture**:
- Error message listing missing columns
- File upload failed indication

---

### TC-A004: Employee Access Management

#### Screenshot 13: Manage Employee Access Page
**Filename**: `TC-A004-01_Manage_Access_Page.png`
**Location**: `/admin/randwater/manage-employee-access`
**Capture**:
- Full page showing employee list
- Search bar
- All columns visible: ID, Name, Grade, Access dates, Status
- Action buttons

#### Screenshot 14: Employee Details Modal
**Filename**: `TC-A004-02_Employee_Details_Modal.png`
**Capture**:
- Modal overlay showing employee details
- Basic Information section
- Access Information section
- Package Details section
- Login Credentials section
- Close button

#### Screenshot 15: Employee with Pending Package
**Filename**: `TC-A004-04_Employee_Pending.png`
**Capture**:
- Employee row showing "Pending" status badge
- Package status indicator
- Days remaining visible

#### Screenshot 16: Employee with Submitted Package
**Filename**: `TC-A004-05_Employee_Submitted.png`
**Capture**:
- Employee row showing "Submitted" status badge
- Submission date visible
- Completed indicator

#### Screenshot 17: Access Expiration Warning
**Filename**: `TC-A004-06_Expiration_Warning.png`
**Capture**:
- Employee with <5 days remaining
- Warning indicator/badge
- Red or yellow highlighting
- Days remaining count

---

### TC-A005: Salary Simulator

#### Screenshot 18: Salary Simulator Interface
**Filename**: `TC-A005-01_Salary_Simulator.png`
**Location**: `/admin/randwater/salary-simulator`
**Capture**:
- Complete simulator interface
- All input fields visible
- Component sections visible
- Calculate button

#### Screenshot 19: Salary Simulator - Data Entered
**Filename**: `TC-A005-02_Simulator_Data_Entered.png`
**Capture**:
- All fields filled with test data
- Amounts entered in all component fields
- Deductions entered

#### Screenshot 20: Salary Simulator - Results
**Filename**: `TC-A005-03_Simulator_Results.png`
**Capture**:
- Calculated results displayed
- Net pay prominently shown
- Tax breakdown visible
- All deductions calculated
- Earnings vs Deductions summary

#### Screenshot 21: Payslip Preview
**Filename**: `TC-A005-09_Payslip_Preview.png`
**Capture**:
- Generated payslip
- Employee information section
- Earnings breakdown
- Deductions breakdown
- Net pay highlighted
- Package breakdown section

---

### TC-A006: Package Management

#### Screenshot 22: Manage Packages Page
**Filename**: `TC-A006-01_Manage_Packages.png`
**Location**: `/manage_packages`
**Capture**:
- List of all packages
- Employee details visible
- TCTC values visible
- Status indicators
- Action buttons

#### Screenshot 23: Package Details View
**Filename**: `TC-A006-02_Package_Details.png`
**Capture**:
- Individual package expanded/opened
- All package components listed
- Component amounts visible
- Total TCTC calculated
- Status displayed

---

### TC-A007: Package Analytics

#### Screenshot 24: Package Analytics Dashboard
**Filename**: `TC-A007-01_Analytics_Dashboard.png`
**Location**: `/package_analytics`
**Capture**:
- Analytics dashboard overview
- Statistics cards
- Charts/graphs (if any)
- Distribution data

#### Screenshot 25: Package Distribution Chart
**Filename**: `TC-A007-02_Package_Distribution.png`
**Capture**:
- Distribution by grade band
- Visual chart/graph
- Legend
- Data labels

---

### TC-A008: Export Functionality

#### Screenshot 26: Export Packages Page
**Filename**: `TC-A008-01_Export_Page.png`
**Capture**:
- Export interface
- Export button
- Options/filters (if any)
- Package count to export

#### Screenshot 27: Export Success
**Filename**: `TC-A008-01_Export_Success.png`
**Capture**:
- Success message
- Download initiated
- File download notification (browser)

#### Screenshot 28: Exported Excel File (Opened)
**Filename**: `TC-A008-02_Exported_File.png`
**Capture**:
- Excel file open showing data
- All columns visible
- Sample data rows
- Format correct

---

## Employee Function Screenshots

### TC-E001: Employee Login

#### Screenshot 29: Employee Login Page
**Filename**: `TC-E001-01_Employee_Login.png`
**Location**: `/employee/login`
**Capture**:
- Employee login page
- Rand Water branding
- Username and password fields
- Login button
- Access expiration notice (if visible)

#### Screenshot 30: Employee Login - Invalid Credentials
**Filename**: `TC-E001-02_Employee_Invalid_Login.png`
**Capture**:
- Error message displayed
- Invalid credentials notice
- Login fields

#### Screenshot 31: Employee Login - Expired Access
**Filename**: `TC-E001-04_Employee_Expired_Access.png`
**Capture**:
- Access expired error message
- Contact HR notice
- Login blocked

---

### TC-E002: Package Builder Interface

#### Screenshot 32: Package Builder Main Interface
**Filename**: `TC-E002-01_Package_Builder_Main.png`
**Location**: `/employee/package-builder`
**Capture**:
- Complete package builder interface
- Header with employee info
- Package overview section
- Adjustable components section
- Fixed components section
- Submit button

#### Screenshot 33: Employee Information Section
**Filename**: `TC-E002-01_Employee_Info.png`
**Capture**:
- Employee ID
- Name
- Grade Band
- Department
- Job Title
- Days remaining badge

#### Screenshot 34: Package Overview Section
**Filename**: `TC-E002-02_Package_Overview.png`
**Capture**:
- TCTC Limit displayed
- Current TCTC displayed
- Remaining budget shown
- Status badge
- Progress bar

#### Screenshot 35: Adjustable Components
**Filename**: `TC-E002-04_Adjustable_Components.png`
**Capture**:
- Basic Salary field (editable)
- Car Allowance field (editable)
- Annual Bonus field (editable)
- Current values visible
- Input fields active

#### Screenshot 36: Fixed Components
**Filename**: `TC-E002-05_Fixed_Components.png`
**Capture**:
- Cellphone Allowance (read-only)
- Data Service Allowance (read-only)
- Housing Allowance (read-only)
- Medical Aid (read-only)
- Lock icons or disabled state visible

---

### TC-E003: Package Component Adjustments

#### Screenshot 37: Before Adjustment
**Filename**: `TC-E003-01_Before_Adjustment.png`
**Capture**:
- Original package values
- TCTC before changes
- Remaining budget before changes

#### Screenshot 38: During Adjustment (Typing)
**Filename**: `TC-E003-02_During_Adjustment.png`
**Capture**:
- Input field being edited
- Cursor in field
- New value being entered

#### Screenshot 39: After Adjustment - Real-time Update
**Filename**: `TC-E003-04_Realtime_Update.png`
**Capture**:
- Updated TCTC value
- Updated remaining budget
- Changed component highlighted
- No page refresh (same session)

#### Screenshot 40: Multiple Adjustments
**Filename**: `TC-E003-06_Multiple_Adjustments.png`
**Capture**:
- Several components changed
- TCTC reflecting all changes
- Remaining budget updated
- All changes visible

---

### TC-E004: Validation - Basic Salary

#### Screenshot 41: Basic Salary - Valid (50-70%)
**Filename**: `TC-E004-01_Basic_Salary_Valid.png`
**Capture**:
- Basic salary within range
- Green checkmark or valid indicator
- No warnings displayed

#### Screenshot 42: Basic Salary - Below 50% Warning
**Filename**: `TC-E004-03_Basic_Salary_Below_Min.png`
**Capture**:
- Basic salary < 50% of TCTC
- Yellow/red warning message
- Warning text clearly visible
- Component highlighted

#### Screenshot 43: Basic Salary - Above 70% Warning
**Filename**: `TC-E004-04_Basic_Salary_Above_Max.png`
**Capture**:
- Basic salary > 70% of TCTC
- Warning message displayed
- Suggested correction (if any)

---

### TC-E005: Validation - Car Allowance

#### Screenshot 44: Car Allowance - Valid (>30%)
**Filename**: `TC-E005-01_Car_Allowance_Valid.png`
**Capture**:
- Car allowance above 30%
- Valid indicator
- No warnings

#### Screenshot 45: Car Allowance - Below 30% Warning
**Filename**: `TC-E005-03_Car_Allowance_Below_Min.png`
**Capture**:
- Car allowance < 30% of TCTC
- Warning message: "Car allowance must be at least 30% of TCTC"
- Red/yellow warning indicator

---

### TC-E006: Validation - Annual Bonus

#### Screenshot 46: Annual Bonus - Valid (10-70%)
**Filename**: `TC-E006-01_Bonus_Valid.png`
**Capture**:
- Bonus within range
- Valid indicator
- No warnings

#### Screenshot 47: Annual Bonus - Below 10% Warning
**Filename**: `TC-E006-03_Bonus_Below_Min.png`
**Capture**:
- Bonus < 10% of TCTC
- Warning message displayed

#### Screenshot 48: Annual Bonus - Above 70% Warning
**Filename**: `TC-E006-04_Bonus_Above_Max.png`
**Capture**:
- Bonus > 70% of TCTC
- Warning message displayed

---

### TC-E007: TCTC Limit Validation

#### Screenshot 49: Package At TCTC Limit
**Filename**: `TC-E007-01_At_TCTC_Limit.png`
**Capture**:
- TCTC exactly at limit
- Remaining budget = R 0
- Progress bar at 100%
- Green valid indicator

#### Screenshot 50: Package Below TCTC Limit
**Filename**: `TC-E007-02_Below_TCTC_Limit.png`
**Capture**:
- TCTC below limit
- Remaining budget > 0
- Progress bar < 100%
- Available budget shown

#### Screenshot 51: Package Exceeds TCTC Limit
**Filename**: `TC-E007-03_Exceeds_TCTC_Limit.png`
**Capture**:
- TCTC over limit
- Remaining budget negative (shown in red)
- Progress bar over 100% or red
- Error message: "TCTC exceeds assigned limit"
- Submit button disabled

---

### TC-E008: Package Submission

#### Screenshot 52: Submit Button (Before Submission)
**Filename**: `TC-E008-01_Submit_Button.png`
**Capture**:
- Submit Package button visible
- Valid package state
- No warnings present

#### Screenshot 53: Submission Confirmation Dialog
**Filename**: `TC-E008-02_Submission_Confirmation.png`
**Capture**:
- Modal/dialog asking for confirmation
- Warning about one-time submission
- Confirm and Cancel buttons
- Package summary in dialog

#### Screenshot 54: Submission Success
**Filename**: `TC-E008-01_Submission_Success.png`
**Capture**:
- Success message displayed
- Confirmation details:
  - Employee ID
  - Final TCTC
  - Net Pay
  - Submission date/time
- Access revoked notice

#### Screenshot 55: Submission Blocked - Warnings Present
**Filename**: `TC-E008-04_Submission_Blocked.png`
**Capture**:
- Submit button disabled or greyed out
- Active warnings displayed
- Error message explaining block

#### Screenshot 56: Login After Submission (Access Revoked)
**Filename**: `TC-E008-06_Access_Revoked.png`
**Capture**:
- Login page
- Error: "Access revoked" or "Package already submitted"
- Cannot access package builder

---

### TC-E009: Calculations

#### Screenshot 57: Net Pay Calculation Display
**Filename**: `TC-E009-01_Net_Pay_Calculation.png`
**Capture**:
- Net pay amount displayed
- Calculation breakdown visible
- Tax amount shown
- UIF amount shown
- Other deductions shown

#### Screenshot 58: Tax Breakdown
**Filename**: `TC-E009-03_Tax_Breakdown.png`
**Capture**:
- Tax calculation details
- SARS bracket applied
- Taxable income shown
- Tax amount calculated

#### Screenshot 59: Package Breakdown
**Filename**: `TC-E009-08_Package_Breakdown.png`
**Capture**:
- TCTC monthly
- Bonus provision monthly
- Basic salary after bonus
- Other earnings
- Employer contributions

---

## Integration Testing Screenshots

#### Screenshot 60: Admin Views Submitted Package
**Filename**: `TC-I002-02_Admin_Views_Submission.png`
**Capture**:
- Admin dashboard showing submitted package
- Submission notification
- Employee moved to "Submitted" section
- Submission timestamp

---

## Security Testing Screenshots

#### Screenshot 61: Unauthorized Access Attempt
**Filename**: `TC-S001-03_Unauthorized_Access.png`
**Capture**:
- Attempted access to protected page without login
- Redirect to login page
- URL showing attempted protected route

#### Screenshot 62: Employee Cannot Access Admin Routes
**Filename**: `TC-S001-02_Employee_Cannot_Access_Admin.png`
**Capture**:
- Employee logged in
- Attempted to access admin URL
- Access denied message or redirect

---

## Error Scenarios Screenshots

#### Screenshot 63: 404 Error Page
**Filename**: `ERROR_404_Page_Not_Found.png`
**Capture**:
- 404 error page
- User-friendly error message
- Navigation options

#### Screenshot 64: 500 Server Error
**Filename**: `ERROR_500_Server_Error.png`
**Capture**:
- 500 error page (if custom page exists)
- Error message
- Support contact info

#### Screenshot 65: Network Error
**Filename**: `ERROR_Network_Error.png`
**Capture**:
- Network connection error
- Browser error message

---

## Browser Compatibility Screenshots

Capture the same key screens in different browsers:

#### Chrome Screenshots
- `BROWSER_Chrome_Admin_Dashboard.png`
- `BROWSER_Chrome_Employee_Package_Builder.png`

#### Firefox Screenshots
- `BROWSER_Firefox_Admin_Dashboard.png`
- `BROWSER_Firefox_Employee_Package_Builder.png`

#### Edge Screenshots
- `BROWSER_Edge_Admin_Dashboard.png`
- `BROWSER_Edge_Employee_Package_Builder.png`

---

## Screenshot Checklist

### Before Starting UAT
- [ ] Set up screen capture tool (Snipping Tool, Greenshot, etc.)
- [ ] Create folders for organizing screenshots
- [ ] Test screenshot file naming convention
- [ ] Prepare annotation tool for highlighting

### During Testing
- [ ] Capture screenshots before each action
- [ ] Capture screenshots after each action
- [ ] Capture all error messages
- [ ] Capture all success messages
- [ ] Annotate important areas
- [ ] Rename files according to convention

### After Testing
- [ ] Review all screenshots for clarity
- [ ] Ensure sensitive data is redacted
- [ ] Organize screenshots by test case
- [ ] Create screenshot index document
- [ ] Archive screenshots with test results

---

## Screenshot Storage Structure

```
UAT_Screenshots/
├── Admin_Functions/
│   ├── TC-A001_Login/
│   ├── TC-A002_Dashboard/
│   ├── TC-A003_SAP_Upload/
│   ├── TC-A004_Employee_Access/
│   ├── TC-A005_Salary_Simulator/
│   ├── TC-A006_Package_Management/
│   ├── TC-A007_Analytics/
│   └── TC-A008_Export/
├── Employee_Functions/
│   ├── TC-E001_Login/
│   ├── TC-E002_Package_Builder/
│   ├── TC-E003_Adjustments/
│   ├── TC-E004_Validation_Basic_Salary/
│   ├── TC-E005_Validation_Car_Allowance/
│   ├── TC-E006_Validation_Bonus/
│   ├── TC-E007_TCTC_Validation/
│   ├── TC-E008_Submission/
│   └── TC-E009_Calculations/
├── Integration_Tests/
├── Security_Tests/
├── Errors/
└── Browser_Compatibility/
```

---

## Screenshot Annotation Guide

### Use annotations to highlight:
1. **Red boxes**: Error messages, warnings, failed validations
2. **Green boxes**: Success messages, valid states, completed actions
3. **Blue arrows**: Important UI elements, navigation paths
4. **Yellow highlights**: Changed values, updated fields
5. **Text labels**: Explanations, notes, expected vs actual

---

## Tools Recommended

1. **Windows**: Snipping Tool, Snip & Sketch, Greenshot
2. **Mac**: Command+Shift+4, Skitch
3. **Cross-platform**: ShareX, LightShot
4. **Annotation**: Greenshot (built-in), Paint, Snagit
5. **Screen Recording**: OBS Studio, Loom (for complex workflows)

---

*This screenshot guide should be used in conjunction with the UAT test cases document to provide complete visual evidence of test execution and results.*

