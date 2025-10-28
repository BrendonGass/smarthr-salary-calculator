# Rand Water System Visual Training Guide

## Table of Contents
1. [Admin Interface Screenshots](#admin-interface-screenshots)
2. [Employee Interface Screenshots](#employee-interface-screenshots)
3. [Step-by-Step Visual Workflows](#step-by-step-visual-workflows)
4. [Common Scenarios with Screenshots](#common-scenarios-with-screenshots)
5. [Error Handling Visual Guide](#error-handling-visual-guide)
6. [Quick Reference Visual Cards](#quick-reference-visual-cards)

---

## Admin Interface Screenshots

### 1. Admin Login Page
```
┌─────────────────────────────────────────────────────────────┐
│                    Rand Water Logo                          │
│                                                             │
│              Package Builder Admin Login                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Username: [RandWaterAdmin                    ]     │    │
│  │ Password: [•••••••••••••••••••••••••••••••••]     │    │
│  │                                                     │    │
│  │              [ Login ]                             │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│              Powered by GoSmartHR                          │
└─────────────────────────────────────────────────────────────┘
```

### 2. Admin Dashboard Overview
```
┌─────────────────────────────────────────────────────────────┐
│  Rand Water Logo    Package Builder Admin Panel    [Logout] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 Statistics Cards                                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │     15      │ │      8      │ │      7      │          │
│  │Active Emp.  │ │ Pending     │ │ Completed   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                             │
│  🛠️ Feature Cards                                          │
│  ┌─────────────────┐ ┌─────────────────┐                    │
│  │ 📤 Upload SAP   │ │ 👥 Manage      │                    │
│  │    Data         │ │    Access      │                    │
│  └─────────────────┘ └─────────────────┘                    │
│  ┌─────────────────┐ ┌─────────────────┐                    │
│  │ 🧮 Salary       │ │ 📥 Export       │                    │
│  │    Simulator    │ │    Packages     │                    │
│  └─────────────────┘ └─────────────────┘                    │
│                                                             │
│  🔔 Recent Notifications                                   │
│  • Employee RW001 submitted package                        │
│  • Employee RW005 access expires in 3 days                 │
│  • New SAP data uploaded successfully                      │
└─────────────────────────────────────────────────────────────┘
```

### 3. Upload SAP Data Interface
```
┌─────────────────────────────────────────────────────────────┐
│                    Upload SAP Data                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📁 File Selection                                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ [Choose File] No file selected                       │    │
│  │ Supported formats: .xlsx, .xls                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  📋 Required Columns:                                       │
│  ✓ Employee ID    ✓ First Name    ✓ Surname                │
│  ✓ Grade Band     ✓ Basic Salary  ✓ CTC                    │
│  ✓ Department     ✓ Job Title     ✓ Allowances             │
│                                                             │
│  ⚠️ Important Notes:                                        │
│  • Only O-Q band employees will be processed              │
│  • Employee access credentials will be generated           │
│  • Access expires after 30 days                           │
│                                                             │
│              [ Upload SAP Data ]                           │
└─────────────────────────────────────────────────────────────┘
```

### 4. Employee Access Management
```
┌─────────────────────────────────────────────────────────────┐
│                Manage Employee Access                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔍 Search: [Employee ID or Name                    ] [🔍] │
│                                                             │
│  📊 Active Employees (15)                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ ID    │ Name        │ Grade │ Access    │ Expires │Status│ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ RW001 │ John Smith  │ O     │ 2024-01-15│ 2024-02-14│✅ │ │
│  │ RW002 │ Jane Doe    │ P     │ 2024-01-16│ 2024-02-15│⚠️ │ │
│  │ RW003 │ Bob Wilson  │ Q     │ 2024-01-17│ 2024-02-16│✅ │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  Actions: [View Details] [Reset Access] [Extend Access]     │
└─────────────────────────────────────────────────────────────┘
```

---

## Employee Interface Screenshots

### 1. Employee Login Page
```
┌─────────────────────────────────────────────────────────────┐
│                    Rand Water Logo                          │
│                                                             │
│              Employee Package Builder Login                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Username: [RW001                            ]     │    │
│  │ Password: [•••••••••••••••••••••••••••••••••]     │    │
│  │                                                     │    │
│  │              [ Login ]                             │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ⏰ Access expires in: 25 days                            │
│              Powered by GoSmartHR                          │
└─────────────────────────────────────────────────────────────┘
```

### 2. Package Builder Main Interface
```
┌─────────────────────────────────────────────────────────────┐
│  Rand Water Logo    Package Builder    Welcome, John Smith   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  👤 Employee Information                                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Employee ID: RW001    │ Grade Band: O                  │ │
│  │ Department: Finance   │ Job Title: Analyst              │ │
│  │ Access Expires: 25 days remaining                      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  📊 Package Overview                                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ TCTC Limit: R 45,000    │ Current TCTC: R 42,500       │ │
│  │ Remaining: R 2,500      │ Status: ⚠️ Pending           │ │
│  │                                                         │ │
│  │ Progress: ████████████████████░░░ 94%                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 3. Package Components Section
```
┌─────────────────────────────────────────────────────────────┐
│                    Package Components                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔧 Adjustable Components                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Basic Salary (TPE)                                      │ │
│  │ [R 25,000.00] ✅ Valid (50-70% of TCTC)                │ │
│  │                                                         │ │
│  │ Car Allowance                                           │ │
│  │ [R 15,000.00] ✅ Valid (Min 30% of TCTC)               │ │
│  │                                                         │ │
│  │ Annual Bonus                                            │ │
│  │ [R 2,500.00] ✅ Valid (10-70% of TCTC)                 │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  🔒 Fixed Components (Cannot be changed)                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Cellphone Allowance: R 500.00                          │ │
│  │ Data Service Allowance: R 300.00                       │ │
│  │ Housing Allowance: R 2,000.00                           │ │
│  │ Medical Aid: R 1,200.00 (Rand Water Medical)            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 4. Package Submission Interface
```
┌─────────────────────────────────────────────────────────────┐
│                    Submit Your Package                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📋 Final Package Summary                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Component              │ Amount                         │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ Basic Salary (TPE)     │ R 25,000.00                   │ │
│  │ Car Allowance          │ R 15,000.00                   │ │
│  │ Annual Bonus           │ R 2,500.00                    │ │
│  │ Cellphone Allowance    │ R 500.00                      │ │
│  │ Data Service Allowance│ R 300.00                      │ │
│  │ Housing Allowance      │ R 2,000.00                    │ │
│  │ Medical Aid            │ R 1,200.00                    │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ Total TCTC             │ R 45,000.00 ✅                │ │
│  │ Net Pay (Monthly)      │ R 32,150.00                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ⚠️ Important: This is a one-time submission!               │
│                                                             │
│  [ Cancel ]              [ Submit Package ]                │
└─────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Visual Workflows

### 1. Admin Workflow: Upload SAP Data
```
Step 1: Access Admin Panel
┌─────────────────┐
│ Admin Login     │
│ [Username]      │
│ [Password]      │
│ [Login]         │
└─────────────────┘
         │
         ▼
Step 2: Navigate to Upload
┌─────────────────┐
│ Dashboard       │
│ [Upload SAP] ←──│
│ [Manage Access] │
│ [Simulator]     │
└─────────────────┘
         │
         ▼
Step 3: Select File
┌─────────────────┐
│ Upload Interface│
│ [Choose File]   │
│ [Upload]        │
└─────────────────┘
         │
         ▼
Step 4: Processing
┌─────────────────┐
│ Processing...   │
│ ✓ Validating    │
│ ✓ Creating     │
│ ✓ Generating    │
└─────────────────┘
         │
         ▼
Step 5: Success
┌─────────────────┐
│ Success!        │
│ 15 employees    │
│ processed       │
│ [OK]            │
└─────────────────┘
```

### 2. Employee Workflow: Package Building
```
Step 1: Employee Login
┌─────────────────┐
│ Employee Login  │
│ [Username]      │
│ [Password]      │
│ [Login]         │
└─────────────────┘
         │
         ▼
Step 2: Review Package
┌─────────────────┐
│ Package Builder │
│ Current Package │
│ TCTC Limit     │
│ Components      │
└─────────────────┘
         │
         ▼
Step 3: Adjust Components
┌─────────────────┐
│ Adjust Salary   │
│ [Basic Salary]  │
│ [Car Allowance] │
│ [Annual Bonus]  │
└─────────────────┘
         │
         ▼
Step 4: Validate Package
┌─────────────────┐
│ Validation      │
│ ✓ All valid     │
│ ✓ Within limits │
│ ✓ Ready to submit│
└─────────────────┘
         │
         ▼
Step 5: Submit Package
┌─────────────────┐
│ Submit Package  │
│ [Confirm]       │
│ [Submit]        │
└─────────────────┘
         │
         ▼
Step 6: Confirmation
┌─────────────────┐
│ Success!        │
│ Package submitted│
│ Access revoked  │
└─────────────────┘
```

---

## Common Scenarios with Screenshots

### Scenario 1: Employee Exceeds TCTC Limit
```
┌─────────────────────────────────────────────────────────────┐
│                    Package Components                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ WARNING: TCTC Limit Exceeded                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Current TCTC: R 47,500                                  │ │
│  │ TCTC Limit: R 45,000                                    │ │
│  │ Excess: R 2,500                                         │ │
│  │                                                         │ │
│  │ Please reduce components to stay within limit           │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  🔧 Adjustable Components                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Basic Salary (TPE)                                      │ │
│  │ [R 28,000.00] ❌ Too high - reduce by R 2,500          │ │
│  │                                                         │ │
│  │ Car Allowance                                           │ │
│  │ [R 15,000.00] ✅ Valid                                  │ │
│  │                                                         │ │
│  │ Annual Bonus                                            │ │
│  │ [R 4,500.00] ✅ Valid                                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  💡 Suggestion: Reduce Basic Salary to R 25,500            │
└─────────────────────────────────────────────────────────────┘
```

### Scenario 2: Car Allowance Below Minimum
```
┌─────────────────────────────────────────────────────────────┐
│                    Package Components                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ WARNING: Car Allowance Below Minimum                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Current Car Allowance: R 10,000                         │ │
│  │ Minimum Required: R 13,500 (30% of TCTC)                │ │
│  │ Shortfall: R 3,500                                      │ │
│  │                                                         │ │
│  │ Please increase car allowance to meet minimum          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  🔧 Adjustable Components                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Basic Salary (TPE)                                      │ │
│  │ [R 25,000.00] ✅ Valid                                  │ │
│  │                                                         │ │
│  │ Car Allowance                                           │ │
│  │ [R 10,000.00] ❌ Below minimum - increase to R 13,500  │ │
│  │                                                         │ │
│  │ Annual Bonus                                            │ │
│  │ [R 2,500.00] ✅ Valid                                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  💡 Suggestion: Increase Car Allowance to R 13,500         │
└─────────────────────────────────────────────────────────────┘
```

### Scenario 3: Successful Package Submission
```
┌─────────────────────────────────────────────────────────────┐
│                    Package Submitted Successfully!          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ Congratulations! Your package has been submitted.       │
│                                                             │
│  📋 Package Summary                                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Employee ID: RW001                                      │ │
│  │ Name: John Smith                                        │ │
│  │ Grade Band: O                                           │ │
│  │                                                         │ │
│  │ Final TCTC: R 45,000.00                                │ │
│  │ Monthly Net Pay: R 32,150.00                           │ │
│  │ Submission Date: 2024-01-20 14:30:25                  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  🔒 Important Information:                                  │
│  • Your access has been automatically revoked              │
│  • Your package cannot be changed                          │
│  • Your package will be uploaded to SAP                   │
│  • You will receive confirmation via email                │
│                                                             │
│  📞 Need Help?                                             │
│  Contact HR: hr@randwater.co.za                            │
│                                                             │
│                    [ Close ]                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Error Handling Visual Guide

### 1. Login Errors
```
┌─────────────────────────────────────────────────────────────┐
│                    Employee Login                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ❌ Login Failed                                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Error: Invalid credentials or access expired            │ │
│  │                                                         │ │
│  │ Possible causes:                                        │ │
│  │ • Incorrect username or password                        │ │
│  │ • Access has expired (30 days)                          │ │
│  │ • Package already submitted                             │ │
│  │                                                         │ │
│  │ Please contact HR for assistance                       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  Username: [RW001                            ]             │
│  Password: [•••••••••••••••••••••••••••••••••]             │
│                                                             │
│              [ Try Again ]                                 │
└─────────────────────────────────────────────────────────────┘
```

### 2. Access Expired Error
```
┌─────────────────────────────────────────────────────────────┐
│                    Access Expired                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⏰ Your access has expired                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Access granted: 2024-01-01                             │ │
│  │ Access expired: 2024-01-31                              │ │
│  │ Days expired: 5 days ago                                │ │
│  │                                                         │ │
│  │ Your 30-day access period has ended.                    │ │
│  │                                                         │ │
│  │ To regain access, please contact HR:                   │ │
│  │ Email: hr@randwater.co.za                               │ │
│  │ Phone: +27 11 123 4567                                  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  [ Contact HR ]                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. Package Already Submitted Error
```
┌─────────────────────────────────────────────────────────────┐
│                    Package Already Submitted                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ Your package has already been submitted                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Submission Date: 2024-01-15 10:30:00                   │ │
│  │ Package Status: Submitted                              │ │
│  │ Processing Status: Ready for SAP upload                 │ │
│  │                                                         │ │
│  │ Your package cannot be changed as it has been           │ │
│  │ submitted and is being processed.                       │ │
│  │                                                         │ │
│  │ If you need to make changes, please contact HR:        │ │
│  │ Email: hr@randwater.co.za                               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  [ Contact HR ]                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Reference Visual Cards

### Admin Quick Reference Card
```
┌─────────────────────────────────────────────────────────────┐
│                    ADMIN QUICK REFERENCE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔑 Login Credentials                                       │
│  Username: RandWaterAdmin                                   │
│  Password: RandWater2024!                                   │
│                                                             │
│  📊 Key Statistics                                           │
│  • Access Duration: 30 days per employee                   │
│  • Grade Bands: O-Q only                                    │
│  • Package Components: 8 main components                   │
│  • Tax Compliance: SARS-compliant                          │
│                                                             │
│  🛠️ Main Functions                                          │
│  • Upload SAP Data → Create employee packages              │
│  • Manage Access → Monitor employee status                 │
│  • Salary Simulator → Test salary scenarios                │
│  • Export Packages → Generate SAP files                    │
│                                                             │
│  ⚠️ Important Notes                                         │
│  • Only O-Q band employees processed                       │
│  • Access auto-expires after 30 days                       │
│  • Packages can only be submitted once                     │
│  • All calculations SARS-compliant                         │
│                                                             │
│  📞 Support                                                 │
│  HR: hr@randwater.co.za                                     │
│  IT: it-support@randwater.co.za                            │
└─────────────────────────────────────────────────────────────┘
```

### Employee Quick Reference Card
```
┌─────────────────────────────────────────────────────────────┐
│                  EMPLOYEE QUICK REFERENCE                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔑 Access Information                                      │
│  • Duration: 30 days from creation                         │
│  • One-time submission only                                │
│  • Access auto-revoked after submission                    │
│                                                             │
│  📊 Package Components                                      │
│  Adjustable:                                                │
│  • Basic Salary (50-70% of TCTC)                          │
│  • Car Allowance (Min 30% of TCTC)                         │
│  • Annual Bonus (10-70% of TCTC)                           │
│                                                             │
│  Fixed (Cannot change):                                     │
│  • Cellphone Allowance                                     │
│  • Data Service Allowance                                  │
│  • Housing Allowance                                       │
│  • Medical Aid                                             │
│                                                             │
│  ⚠️ Validation Rules                                        │
│  • TCTC cannot exceed assigned limit                       │
│  • All components must be within valid ranges              │
│  • Warnings must be resolved before submission            │
│                                                             │
│  📞 Support                                                 │
│  HR: hr@randwater.co.za                                     │
│  IT: it-support@randwater.co.za                            │
└─────────────────────────────────────────────────────────────┘
```

### Troubleshooting Quick Reference
```
┌─────────────────────────────────────────────────────────────┐
│                TROUBLESHOOTING QUICK REFERENCE             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔐 Login Issues                                            │
│  Problem: Cannot login                                      │
│  Solutions:                                                 │
│  • Check username/password                                  │
│  • Verify access hasn't expired                            │
│  • Check if package already submitted                      │
│  • Contact HR for assistance                               │
│                                                             │
│  📊 Package Issues                                          │
│  Problem: Cannot adjust components                          │
│  Solutions:                                                 │
│  • Check if package submitted                              │
│  • Verify access period                                    │
│  • Resolve all warnings                                    │
│  • Refresh page and retry                                  │
│                                                             │
│  ⚠️ Validation Issues                                       │
│  Problem: Warnings displayed                               │
│  Solutions:                                                 │
│  • Read warning message                                    │
│  • Adjust component amounts                                │
│  • Ensure TCTC within limit                               │
│  • Verify all ranges valid                                 │
│                                                             │
│  📤 Submission Issues                                      │
│  Problem: Cannot submit package                            │
│  Solutions:                                                 │
│  • Resolve all warnings                                    │
│  • Check TCTC limits                                       │
│  • Verify package not submitted                            │
│  • Complete all required fields                            │
│                                                             │
│  📞 Emergency Support                                      │
│  HR: hr@randwater.co.za                                     │
│  IT: it-support@randwater.co.za                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Visual Workflow Diagrams

### Complete Admin Workflow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Login     │───▶│  Dashboard   │───▶│ Upload SAP  │
│   Admin     │    │   View       │    │   Data      │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Export    │◀───│  Monitor    │◀───│  Process    │
│  Packages   │    │  Employees  │    │  Employees  │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                           ▼
                   ┌─────────────┐
                   │  Salary     │
                   │  Simulator  │
                   └─────────────┘
```

### Complete Employee Workflow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Login     │───▶│   Review    │───▶│  Adjust     │
│  Employee   │    │  Package    │    │ Components  │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Access     │◀───│  Submit     │◀───│  Validate   │
│  Revoked    │    │  Package    │    │  Package    │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

*This visual training guide provides comprehensive screenshots and visual workflows to help both administrators and employees effectively use the Rand Water Package Builder system. Use these visual references alongside the detailed training guides for complete system understanding.*
