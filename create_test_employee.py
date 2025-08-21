#!/usr/bin/env python3
"""
Script to create a test employee account for the Rand Water Package Builder
"""

import json
from datetime import datetime, timedelta
import os

def create_test_employee():
    """Create a test employee account"""
    
    # Test employee data
    test_employee = {
        'employee_id': 'EMP001',
        'grade_band': 'O',
        'username': 'testemployee',
        'password': 'Test123!',
        'access_granted': datetime.now().isoformat(),
        'access_expires': (datetime.now() + timedelta(days=30)).isoformat(),
        'status': 'ACTIVE',
        'package_submitted': False,
        'submission_date': None,
        'last_login': None
    }
    
    # Create employee access file if it doesn't exist
    access_file = 'employee_access.json'
    if os.path.exists(access_file):
        with open(access_file, 'r') as f:
            access_data = json.load(f)
    else:
        access_data = []
    
    # Check if test employee already exists
    existing_employee = None
    for emp in access_data:
        if emp['employee_id'] == 'EMP001':
            existing_employee = emp
            break
    
    if existing_employee:
        print(f"Test employee already exists:")
        print(f"Username: {existing_employee['username']}")
        print(f"Password: {existing_employee['password']}")
    else:
        # Add test employee
        access_data.append(test_employee)
        
        # Save to file
        with open(access_file, 'w') as f:
            json.dump(access_data, f, indent=2)
        
        print("✅ Test employee account created successfully!")
        print(f"Username: {test_employee['username']}")
        print(f"Password: {test_employee['password']}")
    
    # Create a test package for the employee
    test_package = {
        'employee_id': 'EMP001',
        'grade_band': 'O',
        'tctc_limit': 50000.00,
        'package_components': {
            'basic_salary': 35000.00,
            'provident_fund': 3500.00,
            'car_allowance': 8000.00,
            'cellphone_allowance': 500.00,
            'data_service_allowance': 300.00,
            'housing_allowance': 2000.00,
            'medical_aid': 1200.00,
            'medical_aid_option': 'Rand Water Option A',
            'bonus': 5000.00
        },
        'status': 'ACTIVE',
        'created_date': datetime.now().isoformat(),
        'submitted_date': None,
        'submitted': False
    }
    
    # Create packages file if it doesn't exist
    packages_file = 'employee_packages.json'
    if os.path.exists(packages_file):
        with open(packages_file, 'r') as f:
            packages_data = json.load(f)
    else:
        packages_data = []
    
    # Check if package already exists
    existing_package = None
    for pkg in packages_data:
        if pkg['employee_id'] == 'EMP001':
            existing_package = pkg
            break
    
    if existing_package:
        print(f"Test package already exists for employee {existing_package['employee_id']}")
    else:
        # Add test package
        packages_data.append(test_package)
        
        # Save to file
        with open(packages_file, 'w') as f:
            json.dump(packages_data, f, indent=2)
        
        print("✅ Test package created successfully!")
        print(f"TCTC Limit: R{test_package['tctc_limit']:,.2f}")
        print(f"Basic Salary: R{test_package['package_components']['basic_salary']:,.2f}")
    
    print("\n🌐 You can now test the employee login at:")
    print("http://127.0.0.1:5001/employee/login")
    print("\nUse these credentials:")
    print(f"Username: {test_employee['username']}")
    print(f"Password: {test_employee['password']}")

if __name__ == '__main__':
    create_test_employee()
