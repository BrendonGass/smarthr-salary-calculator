#!/usr/bin/env python3
"""
Create a sample SAP Excel file with the exact field structure provided by the user
"""

import pandas as pd
from datetime import datetime, timedelta
import random

def create_sample_sap_file():
    """Create a sample SAP Excel file with realistic Rand Water data"""
    
    # Sample data for 5 employees across different bands
    sample_data = []
    
    # Employee 1 - O Band
    sample_data.append({
        'EMPLOYEECODE': 'RW001',
        'SURNAME': 'Smith',
        'FIRSTNAME': 'John',
        'TITLE': 'Mr',
        'BIRTHDATE': '1985-05-15',
        'AGE': 39,
        'RACE': 'African',
        'GENDER': 'Male',
        'DISABILITY': 'No',
        'DATEENGAGED': '2015-03-01',
        'YOS': 9,
        'CostCenter': 'CC001',
        'PERSONNELAREADESCRIPTION': 'Operations',
        'PERSONNELSUBAREADESCRIPTION': 'Water Treatment',
        'EMPLOYEEGROUPDESCRIPTION': 'Full Time',
        'EMPLOYEESUBGROUPDESCRIPTION': 'Permanent',
        'JOBID': 'JOB001',
        'JOBSHORT': 'WTO',
        'JOBLONG': 'Water Treatment Operator',
        'HAYUNIT': 'HAY001',
        'POSITIONID': 'POS001',
        'POSTIONSHORT': 'WTO',
        'POSITIONLONG': 'Water Treatment Operator',
        'BAND': 'O',
        'PAYSCALELEVEL': 'O5',
        'PORTFOLIO': 'Operations',
        'DIVISION': 'Water Operations',
        'DEPARTMENT': 'Treatment',
        'ORGANIZATIONALUNIT': 'OU001',
        'ORGANIZATIONALUNITLONG': 'Water Treatment Unit',
        'TPE': 28000.00,
        'CAR': 8000.00,
        'CASH': 2000.00,
        'HOUSING': 3000.00,
        'CRITICALSKILLS': 1500.00,
        'pension': 2800.00,
        'PENSIONOPTION': 'Pension Fund',
        'PENSIONERCONTRIBUTION': 2800.00,
        'PENSIONEECONTRIBUTION': 1400.00,
        'CASHOPTION': 'Standard',
        'MEDICAL': 1200.00,
        'MEDICALOPTION': 'Rand Water Option A',
        'SPOUSE': 'Yes',
        'CHILDREN': '2',
        'ADULTS': '0',
        'MEDICALEECONTRIBUTION': 600.00,
        'MEDICALERCONTRIBUTION': 600.00,
        'UIF': 450.00,
        'GROUPLIFEEECONTRIBUTION': 150.00,
        'GROUPLIFEERCONTRIBUTION': 150.00,
        'BONUSPROVISION': 5000.00,
        'CTC': 45000.00,
        'TCTC': 50000.00,
        'LQ': '40000',
        'MID': '45000',
        'HQ': '50000',
        'LQPACKAGE': 'Basic Package',
        'MIDPACKAGE': 'Standard Package',
        'HQPACKAGE': 'Premium Package',
        'begda': '2024-01-01',
        'endda': '2024-12-31',
        'aedtm': '2024-08-20',
        'CELLPHONEALLOWANCE': 500.00,
        'DATASERVICEALLOWANCE': 300.00
    })
    
    # Employee 2 - P Band
    sample_data.append({
        'EMPLOYEECODE': 'RW002',
        'SURNAME': 'Johnson',
        'FIRSTNAME': 'Sarah',
        'TITLE': 'Ms',
        'BIRTHDATE': '1982-09-22',
        'AGE': 42,
        'RACE': 'Coloured',
        'GENDER': 'Female',
        'DISABILITY': 'No',
        'DATEENGAGED': '2012-07-15',
        'YOS': 12,
        'CostCenter': 'CC002',
        'PERSONNELAREADESCRIPTION': 'Engineering',
        'PERSONNELSUBAREADESCRIPTION': 'Civil Engineering',
        'EMPLOYEEGROUPDESCRIPTION': 'Full Time',
        'EMPLOYEESUBGROUPDESCRIPTION': 'Permanent',
        'JOBID': 'JOB002',
        'JOBSHORT': 'CIV ENG',
        'JOBLONG': 'Civil Engineer',
        'HAYUNIT': 'HAY002',
        'POSITIONID': 'POS002',
        'POSTIONSHORT': 'CIV ENG',
        'POSITIONLONG': 'Civil Engineer',
        'BAND': 'P',
        'PAYSCALELEVEL': 'P3',
        'PORTFOLIO': 'Engineering',
        'DIVISION': 'Infrastructure',
        'DEPARTMENT': 'Civil Engineering',
        'ORGANIZATIONALUNIT': 'OU002',
        'ORGANIZATIONALUNITLONG': 'Infrastructure Development Unit',
        'TPE': 35000.00,
        'CAR': 10000.00,
        'CASH': 3000.00,
        'HOUSING': 4000.00,
        'CRITICALSKILLS': 2000.00,
        'pension': 3500.00,
        'PENSIONOPTION': 'Provident Fund',
        'PENSIONERCONTRIBUTION': 3500.00,
        'PENSIONEECONTRIBUTION': 1750.00,
        'CASHOPTION': 'Enhanced',
        'MEDICAL': 1500.00,
        'MEDICALOPTION': 'Rand Water Option B',
        'SPOUSE': 'Yes',
        'CHILDREN': '1',
        'ADULTS': '1',
        'MEDICALEECONTRIBUTION': 750.00,
        'MEDICALERCONTRIBUTION': 750.00,
        'UIF': 580.00,
        'GROUPLIFEEECONTRIBUTION': 200.00,
        'GROUPLIFEERCONTRIBUTION': 200.00,
        'BONUSPROVISION': 7000.00,
        'CTC': 58000.00,
        'TCTC': 65000.00,
        'LQ': '55000',
        'MID': '60000',
        'HQ': '65000',
        'LQPACKAGE': 'Standard Package',
        'MIDPACKAGE': 'Enhanced Package',
        'HQPACKAGE': 'Executive Package',
        'begda': '2024-01-01',
        'endda': '2024-12-31',
        'aedtm': '2024-08-20',
        'CELLPHONEALLOWANCE': 700.00,
        'DATASERVICEALLOWANCE': 500.00
    })
    
    # Employee 3 - Q Band
    sample_data.append({
        'EMPLOYEECODE': 'RW003',
        'SURNAME': 'Williams',
        'FIRSTNAME': 'Michael',
        'TITLE': 'Dr',
        'BIRTHDATE': '1978-12-05',
        'AGE': 46,
        'RACE': 'White',
        'GENDER': 'Male',
        'DISABILITY': 'No',
        'DATEENGAGED': '2008-11-10',
        'YOS': 16,
        'CostCenter': 'CC003',
        'PERSONNELAREADESCRIPTION': 'Management',
        'PERSONNELSUBAREADESCRIPTION': 'Senior Management',
        'EMPLOYEEGROUPDESCRIPTION': 'Full Time',
        'EMPLOYEESUBGROUPDESCRIPTION': 'Permanent',
        'JOBID': 'JOB003',
        'JOBSHORT': 'GEN MGR',
        'JOBLONG': 'General Manager',
        'HAYUNIT': 'HAY003',
        'POSITIONID': 'POS003',
        'POSTIONSHORT': 'GEN MGR',
        'POSITIONLONG': 'General Manager - Operations',
        'BAND': 'Q',
        'PAYSCALELEVEL': 'Q2',
        'PORTFOLIO': 'Executive',
        'DIVISION': 'Corporate',
        'DEPARTMENT': 'Executive Management',
        'ORGANIZATIONALUNIT': 'OU003',
        'ORGANIZATIONALUNITLONG': 'Executive Management Unit',
        'TPE': 50000.00,
        'CAR': 15000.00,
        'CASH': 5000.00,
        'HOUSING': 6000.00,
        'CRITICALSKILLS': 3000.00,
        'pension': 5000.00,
        'PENSIONOPTION': 'Pension Fund',
        'PENSIONERCONTRIBUTION': 5000.00,
        'PENSIONEECONTRIBUTION': 2500.00,
        'CASHOPTION': 'Executive',
        'MEDICAL': 2000.00,
        'MEDICALOPTION': 'Rand Water Executive Option',
        'SPOUSE': 'Yes',
        'CHILDREN': '3',
        'ADULTS': '2',
        'MEDICALEECONTRIBUTION': 1000.00,
        'MEDICALERCONTRIBUTION': 1000.00,
        'UIF': 850.00,
        'GROUPLIFEEECONTRIBUTION': 300.00,
        'GROUPLIFEERCONTRIBUTION': 300.00,
        'BONUSPROVISION': 12000.00,
        'CTC': 85000.00,
        'TCTC': 95000.00,
        'LQ': '80000',
        'MID': '87500',
        'HQ': '95000',
        'LQPACKAGE': 'Enhanced Package',
        'MIDPACKAGE': 'Executive Package',
        'HQPACKAGE': 'Premium Executive Package',
        'begda': '2024-01-01',
        'endda': '2024-12-31',
        'aedtm': '2024-08-20',
        'CELLPHONEALLOWANCE': 1000.00,
        'DATASERVICEALLOWANCE': 800.00
    })
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Save to Excel file
    filename = 'sample_randwater_sap_data.xlsx'
    df.to_excel(filename, index=False)
    
    print(f"✅ Sample SAP Excel file created: {filename}")
    print(f"📊 Contains {len(sample_data)} employee records")
    print(f"📋 Includes all {len(df.columns)} required fields:")
    
    for i, col in enumerate(df.columns, 1):
        print(f"   {i:2d}. {col}")
    
    print(f"\n🎯 Employee bands included:")
    for band in df['BAND'].unique():
        count = len(df[df['BAND'] == band])
        print(f"   - Band {band}: {count} employee(s)")
    
    return filename

if __name__ == '__main__':
    create_sample_sap_file()
