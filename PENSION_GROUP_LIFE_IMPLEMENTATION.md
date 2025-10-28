# Pension & Group Life Implementation

## Overview

The TCTC calculation now includes employer pension and group life contributions based on Rand Water's Provident Fund and Group Life Scheme rates.

## Rand Water Provident Fund Rates (1 July 2025 - 30 June 2026)

### Contribution Structure
- **Employee Contribution**: 8.67% of TPE (consistent across all options except 'none')
- **Employer Contribution**: Varies by option (Options A, B, D, E, F, G: 17.19%, Option C: 9.450%)

### Pension Options

| Option | Employee Rate | Employer Rate | Description |
|--------|---------------|---------------|-------------|
| A | 8.67% | 17.19% | Full Benefits |
| B | 8.67% | 17.19% | Standard Benefits (Default) |
| C | 8.67% | 9.450% | Reduced Employer Contribution |
| D | 8.67% | 17.19% | Enhanced Benefits |
| E | 8.67% | 17.19% | Option E |
| F | 8.67% | 17.19% | Option F |
| G | 8.67% | 17.19% | Option G |
| SAMWU | 8.67% | 17.19% | SAMWU National Provident Fund |
| none | 0% | 0% | No Pension |

## Rand Water Group Life Scheme 97885

### Standard Option (Default)
- **Provider**: Old Mutual
- **Rate**: R0.771 per R1,000 cover
- **Free Cover Limit**: R16,000,000
- **Employee Contribution**: 0.2% of TPE
- **Employer Contribution**: 0.5% of TPE
- **Death Benefit**: 4x Annual Pensionable Salary
- **Disability**: Permanent Income Protection + Lump Sum (4x APS)
- **Funeral Benefit**: R45.66

### Enhanced Option
- **Employee Contribution**: 1.0% of TPE
- **Employer Contribution**: 2.0% of TPE
- **Death Benefit**: 6x Annual Pensionable Salary
- **Disability**: Permanent Income Protection + Lump Sum (6x APS)
- **Funeral Benefit**: R45.66

### None Option
- **Employee Contribution**: 0% of TPE
- **Employer Contribution**: 0% of TPE
- **No Coverage**

## TCTC Calculation

### Updated Formula
```
TCTC = TPE
     + Car Allowance
     + Cellphone Allowance (read-only)
     + Data Service Allowance (read-only)
     + Housing Allowance (read-only)
     + Medical Aid (read-only)
     + Annual Bonus
     + Employer Pension Contribution (ER% of TPE)
     + Employer Group Life Contribution (ER% of TPE)
```

### Example Calculation for Option B with Standard Group Life

Given:
- TPE: R350,000
- Car Allowance: R100,000
- Fixed allowances: R25,000
- Bonus: R25,000
- Pension Option: B (ER 17.19%)
- Group Life: Standard (ER 0.5%)

```
Pension EE: R350,000 × 8.67%  = R30,345
Pension ER: R350,000 × 17.19% = R60,165

Group Life EE: R350,000 × 0.2% = R700
Group Life ER: R350,000 × 0.5% = R1,750

TCTC = R350,000 + R100,000 + R25,000 + R25,000 + R60,165 + R1,750
     = R561,915
```

## Configuration Management

### Configuration File: `pension_config.json`

The system loads pension and group life rates from a configurable JSON file that can be managed via the Super Admin dashboard.

**Structure:**
```json
{
  "pension_rates": {
    "effective_date": "2025-07-01",
    "expiry_date": "2026-06-30",
    "provider": "Rand Water Provident Fund",
    "options": {
      "B": {
        "employee_rate": 8.67,
        "employer_rate": 17.19,
        "description": "Option B - Standard Benefits"
      }
    }
  },
  "group_life_rates": {
    "effective_date": "2025-07-01",
    "expiry_date": "2026-06-30",
    "provider": "Old Mutual",
    "scheme_code": "97885/G000738D",
    "options": {
      "standard": {
        "employee_rate": 0.2,
        "employer_rate": 0.5,
        "description": "Standard Group Life Cover"
      }
    }
  }
}
```

### Super Admin Management

The Super Admin can:
1. Update pension contribution rates for each option (A-G, SAMWU)
2. Update group life contribution rates (Standard, Enhanced, None)
3. Set effective and expiry dates for rate changes
4. View historical rate changes
5. Edit provider and scheme details

## Implementation Notes

### Key Changes to `models.py`

1. **Updated `_calculate_tctc()` method**:
   - Now calculates pension EE and ER contributions based on TPE
   - Includes group life EE and ER contributions
   - Adds employer contributions to TCTC total

2. **New `_get_pension_rates()` method**:
   - Loads rates from `pension_config.json`
   - Falls back to hardcoded defaults if config unavailable
   - Returns (employee_rate, employer_rate) tuple

3. **New `_get_group_life_rates()` method**:
   - Loads rates from `pension_config.json`
   - Falls back to hardcoded defaults if config unavailable
   - Returns dict with employee and employer rates

4. **Updated `validate_budget_constraints()` method**:
   - Includes employer pension and group life in TCTC calculation
   - Validates against CTC limit including employer costs

### Response Format

When updating a package, the response now includes calculated contributions:

```json
{
  "success": true,
  "package": {
    "current_tctc": 561915.00,
    "package_components": {
      "basic_salary": 350000,
      "car_allowance": 100000,
      "pension_ee": 30345.00,
      "pension_er": 60165.00,
      "group_life_ee": 700.00,
      "group_life_er": 1750.00
    }
  }
}
```

## Testing Checklist

- [ ] TPE changes update pension calculations correctly
- [ ] Pension Option B (default) uses 8.67% EE and 17.19% ER
- [ ] Pension Option C uses reduced ER rate (9.450%)
- [ ] Group Life Standard uses 0.2% EE and 0.5% ER
- [ ] Group Life Enhanced uses 1.0% EE and 2.0% ER
- [ ] TCTC includes employer pension contributions
- [ ] TCTC includes employer group life contributions
- [ ] Configuration loads from pension_config.json
- [ ] Falls back to hardcoded rates if config missing
- [ ] Super Admin can update rates via dashboard
