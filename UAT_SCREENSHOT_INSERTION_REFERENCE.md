# UAT Screenshot Insertion Reference

## Quick Guide: Where to Insert Screenshots in the UAT Document

This reference shows exactly where to insert screenshots when documenting UAT test results.

---

## Screenshot Insertion Format

For each test case, insert screenshots using this format:

```markdown
| Test Case ID | Screenshot | Status |
|--------------|------------|--------|
| TC-A001-01   | ![Admin Login](screenshots/TC-A001-01_Admin_Login_Success.png) | PASS |
```

---

## Admin Functions - Screenshot Locations

### TC-A001: Admin Login
**Insert screenshots after test results table**

Required screenshots:
1. `TC-A001-01_Admin_Login_Page.png` - Login page before login
2. `TC-A001-01_Admin_Dashboard_Success.png` - Dashboard after successful login
3. `TC-A001-02_Admin_Login_Invalid_Credentials.png` - Invalid credentials error
4. `TC-A001-03_Admin_Login_Invalid_Password.png` - Invalid password error

---

### TC-A002: Admin Dashboard
**Insert screenshots in results section**

Required screenshots:
1. `TC-A002-01_Dashboard_Statistics.png` - Statistics cards
2. `TC-A002-02_Feature_Cards.png` - All feature cards
3. `TC-A002-03_Notifications.png` - Notifications section

---

### TC-A003: SAP Data Upload
**Insert screenshots showing upload workflow**

Required screenshots:
1. `TC-A003-01_Upload_SAP_Page.png` - Upload page
2. `TC-A003-02_File_Selected.png` - File selected
3. `TC-A003-03_Upload_Processing.png` - Processing
4. `TC-A003-01_Upload_Success.png` - Success message
5. `TC-A003-04_Upload_Missing_Columns.png` - Error: missing columns
6. `TC-A003-05_Upload_Invalid_File.png` - Error: invalid file

---

### TC-A004: Employee Access Management
**Insert screenshots of employee management interface**

Required screenshots:
1. `TC-A004-01_Manage_Access_Page.png` - Main page
2. `TC-A004-02_Employee_Details_Modal.png` - Employee details
3. `TC-A004-04_Employee_Pending.png` - Pending status
4. `TC-A004-05_Employee_Submitted.png` - Submitted status
5. `TC-A004-06_Expiration_Warning.png` - Expiration warning

---

### TC-A005: Salary Simulator
**Insert screenshots of simulation process**

Required screenshots:
1. `TC-A005-01_Salary_Simulator.png` - Simulator interface
2. `TC-A005-02_Simulator_Data_Entered.png` - Data entered
3. `TC-A005-03_Simulator_Results.png` - Results calculated
4. `TC-A005-09_Payslip_Preview.png` - Payslip preview

---

### TC-A006: Package Management
**Insert screenshots of package views**

Required screenshots:
1. `TC-A006-01_Manage_Packages.png` - Packages list
2. `TC-A006-02_Package_Details.png` - Package details

---

### TC-A007: Package Analytics
**Insert screenshots of analytics**

Required screenshots:
1. `TC-A007-01_Analytics_Dashboard.png` - Analytics overview
2. `TC-A007-02_Package_Distribution.png` - Distribution chart

---

### TC-A008: Export Functionality
**Insert screenshots of export process**

Required screenshots:
1. `TC-A008-01_Export_Page.png` - Export interface
2. `TC-A008-01_Export_Success.png` - Export success
3. `TC-A008-02_Exported_File.png` - Opened Excel file

---

## Employee Functions - Screenshot Locations

### TC-E001: Employee Login
**Insert screenshots after test cases**

Required screenshots:
1. `TC-E001-01_Employee_Login.png` - Login page
2. `TC-E001-02_Employee_Invalid_Login.png` - Invalid credentials
3. `TC-E001-04_Employee_Expired_Access.png` - Expired access error

---

### TC-E002: Package Builder Interface
**Insert screenshots showing complete interface**

Required screenshots:
1. `TC-E002-01_Package_Builder_Main.png` - Full interface
2. `TC-E002-01_Employee_Info.png` - Employee info section
3. `TC-E002-02_Package_Overview.png` - Package overview
4. `TC-E002-04_Adjustable_Components.png` - Adjustable components
5. `TC-E002-05_Fixed_Components.png` - Fixed components

---

### TC-E003: Package Component Adjustments
**Insert screenshots showing adjustment workflow**

Required screenshots:
1. `TC-E003-01_Before_Adjustment.png` - Before changes
2. `TC-E003-02_During_Adjustment.png` - During editing
3. `TC-E003-04_Realtime_Update.png` - After changes
4. `TC-E003-06_Multiple_Adjustments.png` - Multiple changes

---

### TC-E004: Validation - Basic Salary
**Insert screenshots of validation states**

Required screenshots:
1. `TC-E004-01_Basic_Salary_Valid.png` - Valid state
2. `TC-E004-03_Basic_Salary_Below_Min.png` - Below minimum warning
3. `TC-E004-04_Basic_Salary_Above_Max.png` - Above maximum warning

---

### TC-E005: Validation - Car Allowance
**Insert screenshots of car allowance validation**

Required screenshots:
1. `TC-E005-01_Car_Allowance_Valid.png` - Valid state
2. `TC-E005-03_Car_Allowance_Below_Min.png` - Below minimum warning

---

### TC-E006: Validation - Annual Bonus
**Insert screenshots of bonus validation**

Required screenshots:
1. `TC-E006-01_Bonus_Valid.png` - Valid state
2. `TC-E006-03_Bonus_Below_Min.png` - Below minimum
3. `TC-E006-04_Bonus_Above_Max.png` - Above maximum

---

### TC-E007: TCTC Limit Validation
**Insert screenshots of TCTC validation**

Required screenshots:
1. `TC-E007-01_At_TCTC_Limit.png` - At limit (100%)
2. `TC-E007-02_Below_TCTC_Limit.png` - Below limit
3. `TC-E007-03_Exceeds_TCTC_Limit.png` - Exceeded limit (error)

---

### TC-E008: Package Submission
**Insert screenshots of submission workflow**

Required screenshots:
1. `TC-E008-01_Submit_Button.png` - Submit button
2. `TC-E008-02_Submission_Confirmation.png` - Confirmation dialog
3. `TC-E008-01_Submission_Success.png` - Success message
4. `TC-E008-04_Submission_Blocked.png` - Submission blocked
5. `TC-E008-06_Access_Revoked.png` - Access revoked after submission

---

### TC-E009: Calculations
**Insert screenshots of calculations**

Required screenshots:
1. `TC-E009-01_Net_Pay_Calculation.png` - Net pay display
2. `TC-E009-03_Tax_Breakdown.png` - Tax calculation
3. `TC-E009-08_Package_Breakdown.png` - Package breakdown

---

## Integration & Security Tests

### Integration Tests
Required screenshots:
1. `TC-I002-02_Admin_Views_Submission.png` - Admin sees employee submission

### Security Tests
Required screenshots:
1. `TC-S001-03_Unauthorized_Access.png` - Unauthorized access blocked
2. `TC-S001-02_Employee_Cannot_Access_Admin.png` - Employee blocked from admin

---

## Browser Compatibility Screenshots

Add a browser compatibility section with:
1. `BROWSER_Chrome_Admin_Dashboard.png`
2. `BROWSER_Firefox_Admin_Dashboard.png`
3. `BROWSER_Edge_Admin_Dashboard.png`
4. `BROWSER_Chrome_Employee_Package_Builder.png`
5. `BROWSER_Firefox_Employee_Package_Builder.png`
6. `BROWSER_Edge_Employee_Package_Builder.png`

---

## Example: Complete Test Case with Screenshots

```markdown
### TC-A001: Admin Login

| Test Case ID | Test Description | Expected Result | Screenshot | Status |
|--------------|-----------------|-----------------|------------|--------|
| TC-A001-01 | Admin login with valid credentials | Dashboard loads successfully | ![Success](screenshots/TC-A001-01_Admin_Dashboard_Success.png) | ✅ PASS |
| TC-A001-02 | Admin login with invalid username | Error message displayed | ![Error](screenshots/TC-A001-02_Admin_Login_Invalid_Credentials.png) | ✅ PASS |

**Test Evidence:**

**Before Login:**
![Admin Login Page](screenshots/TC-A001-01_Admin_Login_Page.png)
*Figure 1: Admin login page showing Rand Water branding and login fields*

**Invalid Credentials:**
![Invalid Login](screenshots/TC-A001-02_Admin_Login_Invalid_Credentials.png)
*Figure 2: Error message displayed for invalid credentials*

**Successful Login:**
![Dashboard](screenshots/TC-A001-01_Admin_Dashboard_Success.png)
*Figure 3: Admin dashboard after successful login showing all features*

**Test Result:** ✅ PASS
**Tester:** [Name]
**Date:** [Date]
**Notes:** All login scenarios tested successfully
```

---

## Screenshot Naming Convention Reminder

```
Format: TC-[TestCaseID]_[Description]_[Status].png

Examples:
- TC-A001-01_Admin_Login_Success_PASS.png
- TC-E007-03_Exceeds_TCTC_Limit_FAIL.png
- TC-A003-01_Upload_Success_PASS.png
```

---

## Creating Evidence Package

When finalizing UAT:

1. **Create folder structure:**
   ```
   UAT_Evidence/
   ├── Screenshots/
   │   ├── Admin/
   │   ├── Employee/
   │   └── Integration/
   ├── Test_Results/
   │   └── RANDWATER_UAT_DOCUMENT.md (with screenshots)
   └── Summary/
       └── UAT_Summary_Report.pdf
   ```

2. **Insert screenshots in UAT document**
3. **Generate PDF with embedded screenshots**
4. **Create summary report with key screenshots**
5. **Archive all evidence**

---

*Use this reference to ensure all test cases have proper screenshot documentation for UAT sign-off.*

