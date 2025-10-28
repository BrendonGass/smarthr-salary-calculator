import json
import random
import string

# Load SAP uploads to get employee data
with open('sap_uploads.json', 'r') as f:
    sap_uploads = json.load(f)

if sap_uploads:
    latest_upload = max(sap_uploads, key=lambda x: x['upload_date'])
    employee_data = latest_upload['employee_data']
    
    # Create employee access records
    employee_access = []
    
    for emp in employee_data:
        employee_id = emp['EMPLOYEECODE']
        first_name = emp['FIRSTNAME']
        surname = emp['SURNAME']
        band = emp['BAND']
        
        # Only create access for O, P, Q bands
        if band.upper() in ['O', 'P', 'Q']:
            # Generate username (first letter of first name + surname)
            username = f"{first_name[0].lower()}{surname.lower()}"
            
            # Generate password (8 characters)
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            access_record = {
                'employee_id': employee_id,
                'username': username,
                'password': password,
                'first_name': first_name,
                'surname': surname,
                'band': band,
                'status': 'ACTIVE',
                'access_granted': '2025-10-23',
                'access_expires': '2025-11-23',
                'created_date': '2025-10-23T12:00:00'
            }
            
            employee_access.append(access_record)
            print(f"Created access for {employee_id}: {first_name} {surname} - Username: {username}, Password: {password}")
    
    # Save employee access records
    with open('employee_access.json', 'w') as f:
        json.dump(employee_access, f, indent=2)
    
    print(f"\nCreated {len(employee_access)} employee access records")
else:
    print("No SAP uploads found")
