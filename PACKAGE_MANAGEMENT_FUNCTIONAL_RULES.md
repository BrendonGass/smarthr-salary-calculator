# Package Management (TCTC Modeller) – Functional Rules

## 1. Context

This module manages employee package modelling (TCTC) within both:

- **Admin Dashboard** – where administrators can view and adjust employee packages
  - All edits must record an audit trail (timestamp, admin username, and change summary)
  - Employees are notified when a change is made

- **Employee Dashboard** – where employees can view their own packages and simulate changes within allowed limits
  - The admin and employee views share identical calculation logic — only the editing permissions and audit tracking differ

## 2. Core Definitions

| Term | Definition |
|------|------------|
| **CTC (Cost to Company)** | Fixed upper limit of the employee's package — cannot be changed |
| **TPE (Total Pensionable Emolument)** | Editable portion of the package within allowed range |
| **SAP Data** | Imported from the HR system (Excel upload). Fields like housing, data, cellphone allowances are read-only |

## 3. Editable Fields and Rules

| Component | Editable? | Validation / Rules | Notes |
|-----------|-----------|-------------------|-------|
| **Total Pensionable Emolument (TPE)** | ✅ Editable | For O–Q Band employees: warn if TPE < 50% or > 70% of CTC | Drives pension and group life calculations |
| **Car Allowance** | ✅ Editable | Warn if < 30% of CTC | 80% taxable portion |
| **Cellphone Allowance** | ❌ Read-only | Display SAP value only | Cannot edit |
| **Data Service Allowance** | ❌ Read-only | Display SAP value only | Cannot edit |
| **Housing Allowance** | ❌ Read-only | Display SAP value only | Cannot edit |
| **Retirement Fund Name** | 🔸 Modeller: Read-only<br>🔸 Net Pay Calculator: Editable | Options: RWPROV, RWMPPROV, SAMWU | Changes allowed only in Salary Simulator |
| **Retirement Fund Option** | 🔸 Modeller: Read-only<br>🔸 Net Pay Calculator: Editable | Options: A, B, D, E, F, G, C, none, SAMWU | Determines contribution % |
| **Retirement Fund Value** | Auto-calculated | EE% * TPE and ER% * TPE based on selected option | Example: 7.5% of R10 000 → R750 |
| **Annual Bonus (13th Cheque)** | ✅ Editable | Warn if < 10% or > 70% of CTC (O–Q Bands only) | Can choose between "monthly" or "annual" |
| **Group Life Option** | ✅ Editable | "Standard", "Enhanced", or "None" | Adjusts ER/EE contributions automatically |

## 4. Automatic Calculations

### Pension Contributions

Based on the current retirement fund option.

Example defaults:
- **Option A** → ER 15%, EE 7.5%
- **Option B** → ER 17%, EE 8.5%
- **Option C** → ER 20%, EE 10%

### Group Life

- **Standard** → ER 0.5%, EE 0.2% of TPE
- **Enhanced** → ER 1%, EE 0.5% of TPE

### Standard Deductions

- **UIF** = 1% of income (max R177.12)
- **PAYE** = simplified SARS calculation (use full tax tables when integrating)

### Bonus Provision

- If "monthly", full bonus divided by 12 for calculation

### Cash Component

```
CTC − (sum of allowances + ER contributions + SAP fixed values)
```

## 5. Validation Warnings

For employees in O–Q Bands, show contextual warnings (non-blocking):

- ⚠ TPE below 50% or above 70% of CTC
- ⚠ Car Allowance below 30% of CTC
- ⚠ Bonus below 10% or above 70% of CTC

Warnings are non-blocking; the user may still save.

## 6. Audit Trail Requirements (Admin only)

Each admin edit must log:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "admin_user": "randwater_admin",
  "employee_id": "RW001234",
  "changes": [
    "TPE: R10 000 → R12 000",
    "Bonus Type: Monthly → Annual"
  ]
}
```

**Requirements:**
- Entries display in reverse chronological order within the Audit Trail panel
- Each entry shows: timestamp, admin username, employee ID, and summary of changes

## 7. Integration Notes

- All fixed allowances and fund data are read from the SAP upload (Excel)
- The `/api/package-details/<employee_id>` endpoint returns both SAP and modelled data
- The front-end JS dynamically:
  - Recalculates all totals on input/change events
  - Displays warnings and recalculated percentages
  - Prevents exceeding the CTC limit visually (red highlight)

## 8. Excel Sheet Reference

- **Sheet 1**: SAP raw employee data
- **Sheet 2**: Example tax and pension calculation for employee RW001.1

## 9. Implementation Reference

### Key Files:
- `models.py` - `PackageManager` class with `validate_budget_constraints()` method
- `randwater_package_builder.py` - Admin routes and package editing logic
- `templates/manage_packages.html` - Admin interface for package management

### Key Methods:
- `update_employee_package()` - Handles updates with validation
- `validate_budget_constraints()` - Enforces rules and warnings
- `add_audit_entry()` - Creates audit trail entries
