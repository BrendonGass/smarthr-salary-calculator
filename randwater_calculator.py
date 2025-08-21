from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, g
import json
import math
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import requests
import os
from datetime import datetime
import logging
import csv
from typing import Dict, List, Optional

app = Flask(__name__)
app.secret_key = 'randwater-super-secret-key-2024'  # Change this in production

# Rand Water specific configuration
RANDWATER_CONFIG = {
    'company_name': 'Rand Water',
    'company_logo': '/static/images/randwater-logo.png',
    'brand_colors': {
        'primary': '#0066CC',
        'secondary': '#00A3E0',
        'accent': '#FF6600'
    },
    'sap_config': {
        'base_url': os.environ.get('RANDWATER_SAP_URL', 'https://sap.randwater.co.za'),
        'username': os.environ.get('RANDWATER_SAP_USER', 'randwater_user'),
        'password': os.environ.get('RANDWATER_SAP_PASS', 'randwater_pass'),
        'client': os.environ.get('RANDWATER_SAP_CLIENT', '100')
    }
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tax settings file for Rand Water
TAX_SETTINGS_FILE = 'randwater_tax_settings.json'

def load_tax_settings():
    """Load Rand Water specific tax settings"""
    try:
        with open(TAX_SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            "rebate_primary": 17235,
            "rebate_secondary": 9444,
            "rebate_tertiary": 3145,
            "uif_ceiling": 177.12,
            "medical_main": 364,
            "medical_first": 364,
            "medical_additional": 246
        }

class RandWaterSAPIntegration:
    """Rand Water specific SAP integration"""
    
    def __init__(self, sap_config: Dict):
        self.sap_base_url = sap_config.get('base_url')
        self.sap_username = sap_config.get('username')
        self.sap_password = sap_config.get('password')
        self.sap_client = sap_config.get('client')
        self.logger = logging.getLogger(__name__)
        
    def get_employee_data(self, employee_id: str) -> Dict:
        """Fetch Rand Water employee data from SAP"""
        try:
            # Rand Water specific SAP endpoint
            endpoint = f"{self.sap_base_url}/sap/opu/odata/sap/ZRW_EMPLOYEE_SRV/EmployeeSet('{employee_id}')"
            
            headers = {
                'Authorization': f'Basic {self._get_auth_token()}',
                'Accept': 'application/json'
            }
            
            response = requests.get(endpoint, headers=headers, timeout=30)
            response.raise_for_status()
            
            employee_data = response.json()
            return self._transform_randwater_employee_data(employee_data)
            
        except Exception as e:
            self.logger.error(f"Error fetching Rand Water employee data: {str(e)}")
            return {}
    
    def get_salary_data(self, employee_id: str) -> Dict:
        """Fetch Rand Water salary and benefits data from SAP"""
        try:
            endpoint = f"{self.sap_base_url}/sap/opu/odata/sap/ZRW_SALARY_SRV/SalarySet"
            params = {
                '$filter': f"EmployeeId eq '{employee_id}'",
                '$select': 'BasicSalary,Allowances,Deductions,EmployerContributions,RandWaterBenefits'
            }
            
            headers = {
                'Authorization': f'Basic {self._get_auth_token()}',
                'Accept': 'application/json'
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            salary_data = response.json()
            return self._transform_randwater_salary_data(salary_data)
            
        except Exception as e:
            self.logger.error(f"Error fetching Rand Water salary data: {str(e)}")
            return {}
    
    def submit_package_changes(self, employee_id: str, package_data: Dict) -> bool:
        """Submit Rand Water employee package changes back to SAP"""
        try:
            sap_data = self._transform_to_randwater_sap_format(package_data)
            
            endpoint = f"{self.sap_base_url}/sap/opu/odata/sap/ZRW_PACKAGE_SRV/PackageSet"
            
            headers = {
                'Authorization': f'Basic {self._get_auth_token()}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            payload = {
                'EmployeeId': employee_id,
                'PackageData': sap_data,
                'SubmissionDate': datetime.now().isoformat(),
                'Status': 'SUBMITTED',
                'Company': 'RANDWATER'
            }
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            self.logger.info(f"Rand Water package changes submitted successfully for employee {employee_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error submitting Rand Water package changes: {str(e)}")
            return False
    
    def generate_randwater_export_file(self, completed_packages: List[Dict]) -> str:
        """Generate Rand Water specific SAP export file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"randwater_sap_export_{timestamp}.csv"
            filepath = f"exports/{filename}"
            
            os.makedirs("exports", exist_ok=True)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'EmployeeId', 'FirstName', 'Surname', 'JobTitle', 'Department',
                    'BasicSalary', 'TotalEarnings', 'TotalDeductions', 'NetPay',
                    'TotalEmployer', 'CTC', 'Status', 'SubmissionDate', 'Company'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for package in completed_packages:
                    writer.writerow({
                        'EmployeeId': package.get('employee_id'),
                        'FirstName': package.get('first_name'),
                        'Surname': package.get('surname'),
                        'JobTitle': package.get('job_title'),
                        'Department': package.get('department'),
                        'BasicSalary': package.get('basic_salary'),
                        'TotalEarnings': package.get('total_earnings'),
                        'TotalDeductions': package.get('total_deductions'),
                        'NetPay': package.get('net_pay'),
                        'TotalEmployer': package.get('total_employer'),
                        'CTC': package.get('ctc'),
                        'Status': package.get('status'),
                        'SubmissionDate': package.get('submission_date'),
                        'Company': 'RANDWATER'
                    })
            
            self.logger.info(f"Rand Water SAP export file generated: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error generating Rand Water SAP export file: {str(e)}")
            return ""
    
    def _get_auth_token(self) -> str:
        """Get Rand Water SAP authentication token"""
        import base64
        credentials = f"{self.sap_username}:{self.sap_password}"
        return base64.b64encode(credentials.encode()).decode()
    
    def _transform_randwater_employee_data(self, sap_data: Dict) -> Dict:
        """Transform Rand Water SAP employee data to calculator format"""
        return {
            'employee_id': sap_data.get('EmployeeId'),
            'first_name': sap_data.get('FirstName'),
            'surname': sap_data.get('LastName'),
            'id_number': sap_data.get('IdNumber'),
            'email': sap_data.get('Email'),
            'job_title': sap_data.get('JobTitle'),
            'department': sap_data.get('Department'),
            'start_date': sap_data.get('StartDate'),
            'age': sap_data.get('Age'),
            'company': 'RANDWATER'
        }
    
    def _transform_randwater_salary_data(self, sap_data: Dict) -> Dict:
        """Transform Rand Water SAP salary data to calculator format"""
        return {
            'basic_salary': sap_data.get('BasicSalary', 0),
            'allowances': sap_data.get('Allowances', []),
            'deductions': sap_data.get('Deductions', []),
            'employer_contributions': sap_data.get('EmployerContributions', []),
            'randwater_benefits': sap_data.get('RandWaterBenefits', []),
            'ctc': sap_data.get('CTC', 0)
        }
    
    def _transform_to_randwater_sap_format(self, calculator_data: Dict) -> Dict:
        """Transform calculator data to Rand Water SAP format"""
        return {
            'BasicSalary': calculator_data.get('basic_salary'),
            'Allowances': calculator_data.get('earnings', []),
            'Deductions': calculator_data.get('deductions', []),
            'EmployerContributions': calculator_data.get('employer', []),
            'CTC': calculator_data.get('ctc_total_val'),
            'NetPay': calculator_data.get('net_pay_val'),
            'Company': 'RANDWATER'
        }

# Initialize Rand Water SAP integration
randwater_sap = RandWaterSAPIntegration(RANDWATER_CONFIG['sap_config'])

@app.before_request
def before_request():
    """Handle Rand Water ESS SSO token and user authentication"""
    sso_token = request.args.get('sso_token') or request.headers.get('X-SSO-Token')
    user_id = request.args.get('user_id') or request.headers.get('X-User-ID')
    
    if sso_token and user_id:
        if validate_randwater_sso_token(sso_token, user_id):
            session['user_id'] = user_id
            session['authenticated'] = True
            session['company'] = 'RANDWATER'
            g.current_user = user_id
        else:
            return jsonify({'error': 'Invalid Rand Water SSO token'}), 401

def validate_randwater_sso_token(token, user_id):
    """Validate Rand Water SSO token with ESS system"""
    try:
        # Rand Water specific SSO validation
        response = requests.post(
            'https://ess.randwater.co.za/validate-token',
            json={'token': token, 'user_id': user_id, 'company': 'RANDWATER'},
            timeout=5
        )
        return response.status_code == 200
    except:
        # For development, accept any token
        return True

@app.route('/')
def index():
    """Rand Water calculator main entry point"""
    return redirect(url_for('randwater_calculator'))

@app.route('/calculator')
def randwater_calculator():
    """Rand Water specific calculator view"""
    return render_template('randwater_calculator.html', config=RANDWATER_CONFIG)

@app.route('/api/randwater/employee/<employee_id>')
def get_randwater_employee_data(employee_id):
    """API endpoint to get Rand Water employee data from SAP"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        employee_data = randwater_sap.get_employee_data(employee_id)
        salary_data = randwater_sap.get_salary_data(employee_id)
        
        if not employee_data:
            return jsonify({'error': 'Rand Water employee not found'}), 404
        
        combined_data = {**employee_data, **salary_data}
        return jsonify(combined_data)
        
    except Exception as e:
        logger.error(f"Error fetching Rand Water employee data: {str(e)}")
        return jsonify({'error': 'Failed to fetch Rand Water employee data'}), 500

@app.route('/api/randwater/package/submit', methods=['POST'])
def submit_randwater_package():
    """Submit Rand Water employee package changes to SAP"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        package_data = data.get('package_data')
        
        if not employee_id or not package_data:
            return jsonify({'error': 'Missing required data'}), 400
        
        success = randwater_sap.submit_package_changes(employee_id, package_data)
        
        if success:
            save_randwater_completed_package(employee_id, package_data)
            return jsonify({'message': 'Rand Water package submitted successfully'})
        else:
            return jsonify({'error': 'Failed to submit Rand Water package'}), 500
            
    except Exception as e:
        logger.error(f"Error submitting Rand Water package: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/randwater/packages/export')
def export_randwater_packages():
    """Export all completed Rand Water packages for SAP upload"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        completed_packages = get_all_randwater_completed_packages()
        
        if not completed_packages:
            return jsonify({'error': 'No completed Rand Water packages found'}), 404
        
        export_file = randwater_sap.generate_randwater_export_file(completed_packages)
        
        if export_file:
            return send_file(
                export_file,
                as_attachment=True,
                download_name=f"randwater_sap_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
        else:
            return jsonify({'error': 'Failed to generate Rand Water export file'}), 500
            
    except Exception as e:
        logger.error(f"Error exporting Rand Water packages: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/calculate/randwater', methods=['POST'])
def calculate_randwater():
    """Rand Water specific calculation endpoint"""
    try:
        form = request.form
        settings = load_tax_settings()

        # Parse Rand Water specific components
        earnings = parse_group(form, prefix="earnings")
        deductions = parse_group(form, prefix="deductions")
        employer = parse_group(form, prefix="employer")
        randwater_benefits = parse_group(form, prefix="randwater_benefits")

        gross = sum(val for label, val in earnings)
        total_deductions = sum(val for label, val in deductions)
        total_employer = sum(val for label, val in employer)
        total_randwater_benefits = sum(val for label, val in randwater_benefits)

        # Rand Water specific UIF calculation
        uif_cap = settings.get('uif_ceiling', 17712)
        uif = min(uif_cap, gross * 0.01)
        
        # Get age and medical info
        age = int(form.get("age", 0))
        has_medical = form.get("has_medical", "no") == "yes"
        dependants = int(form.get("dependants", 0))

        # Calculate taxable income (including travel allowance)
        travel_allowance = next((val for label, val in earnings if 'transport' in label.lower()), 0)
        annual_travel_taxable = travel_allowance * 12 * 0.8
        gross_excluding_travel = gross - travel_allowance
        taxable_income = gross_excluding_travel * 12 + annual_travel_taxable

        # Calculate pension deductions
        pension_employee = next((val for label, val in deductions if 'pension' in label.lower()), 0)
        pension_employer = next((val for label, val in employer if 'pension' in label.lower()), 0)
        
        total_pension_deductible = (pension_employee + pension_employer) * 12
        total_pension_deductible = min(total_pension_deductible, 0.275 * taxable_income, 350000)
        
        taxable_income -= total_pension_deductible

        # PAYE calculation using SARS brackets
        annual_tax = calculate_tax(taxable_income, settings)

        # Apply rebates
        rebate = settings['rebate_primary']
        if age >= 65:
            rebate += settings['rebate_secondary']
        if age >= 75:
            rebate += settings['rebate_tertiary']

        annual_tax -= rebate
        annual_tax = max(0, annual_tax)

        # Medical tax credits
        if has_medical:
            credit = settings['medical_main']
            if dependants >= 1:
                credit += settings['medical_first']
            if dependants > 1:
                credit += (dependants - 1) * settings['medical_additional']
            annual_tax -= credit * 12

        annual_tax = max(0, annual_tax)
        monthly_tax = round(annual_tax / 12, 2)
        total_deductions += monthly_tax + uif

        net_pay = gross - total_deductions

        return jsonify({
            "earnings": gross,
            "deductions": total_deductions,
            "employer": total_employer,
            "randwater_benefits": total_randwater_benefits,
            "uif": round(uif, 2),
            "monthly_tax": monthly_tax,
            "take_home": round(net_pay, 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

def parse_group(form, prefix):
    """Parse form groups for Rand Water calculator"""
    result = []
    i = 0
    while True:
        label_key = f"{prefix}[{i}][label]"
        value_key = f"{prefix}[{i}][value]"
        if label_key not in form or value_key not in form:
            break
        try:
            label = form[label_key]
            value = float(form[value_key])
            result.append((label, value))
        except:
            pass
        i += 1
    return result

def calculate_tax(income, settings):
    """Calculate tax using SARS brackets"""
    try:
        tax_brackets = json.loads(settings.get('tax_brackets', '[]'))
        
        if tax_brackets:
            tax = 0
            previous_threshold = 0
            
            for bracket in tax_brackets:
                threshold = bracket['threshold']
                rate = bracket['rate'] / 100
                
                if income > previous_threshold:
                    taxable_in_bracket = min(income - previous_threshold, threshold - previous_threshold)
                    tax += taxable_in_bracket * rate
                
                if income <= threshold:
                    break
                previous_threshold = threshold
            
            return tax
    except:
        pass
    
    # Fallback to default SARS brackets
    brackets = [
        (0, 237100, 0.18, 0),
        (237101, 370500, 0.26, 42678),
        (370501, 512800, 0.31, 77362),
        (512801, 673000, 0.36, 121475),
        (673001, 857900, 0.39, 179147),
        (857901, 1817000, 0.41, 251258),
        (1817001, float('inf'), 0.45, 644489),
    ]
    
    for lower, upper, rate, base in brackets:
        if income <= upper:
            return base + (income - lower) * rate
    return 0

def save_randwater_completed_package(employee_id, package_data):
    """Save completed Rand Water package to local storage"""
    try:
        completed_packages_file = 'randwater_completed_packages.json'
        
        if os.path.exists(completed_packages_file):
            with open(completed_packages_file, 'r') as f:
                packages = json.load(f)
        else:
            packages = []
        
        package_record = {
            'employee_id': employee_id,
            'package_data': package_data,
            'submission_date': datetime.now().isoformat(),
            'status': 'COMPLETED',
            'company': 'RANDWATER'
        }
        
        packages.append(package_record)
        
        with open(completed_packages_file, 'w') as f:
            json.dump(packages, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error saving Rand Water completed package: {str(e)}")

def get_all_randwater_completed_packages():
    """Get all completed Rand Water packages"""
    try:
        completed_packages_file = 'randwater_completed_packages.json'
        
        if os.path.exists(completed_packages_file):
            with open(completed_packages_file, 'r') as f:
                return json.load(f)
        else:
            return []
            
    except Exception as e:
        logger.error(f"Error loading Rand Water completed packages: {str(e)}")
        return []

def get_active_randwater_employees():
    """Get active Rand Water employees from uploaded SAP data"""
    try:
        # First, try to get employees from completed packages
        completed_packages = get_all_randwater_completed_packages()
        
        if completed_packages:
            # Convert completed packages to employee format
            employees = []
            for package in completed_packages:
                # Check if this employee already exists
                existing_employee = next((e for e in employees if e['employee_id'] == package['employee_id']), None)
                
                if not existing_employee:
                    # Create employee record from package data
                    employee = {
                        'employee_id': package['employee_id'],
                        'first_name': package.get('employee_name', '').split()[0] if package.get('employee_name') else '',
                        'surname': ' '.join(package.get('employee_name', '').split()[1:]) if package.get('employee_name') and len(package.get('employee_name', '').split()) > 1 else '',
                        'grade_band': package.get('grade_band', 'O-Q'),
                        'department': package.get('department', 'General'),
                        'job_title': package.get('job_title', 'Employee'),
                        'basic_salary': package.get('basic_salary', 0),
                        'ctc': package.get('ctc', 0),
                        'access_granted': package.get('submission_date', '2024-08-21'),
                        'access_expires': '2024-12-31',
                        'days_remaining': 132,  # Mock calculation
                        'package_submitted': package.get('status') == 'COMPLETED',
                        'is_expired': False
                    }
                    employees.append(employee)
            
            return employees
        
        # If no completed packages, check if we have uploaded SAP data
        if session.get('last_upload'):
            try:
                import pandas as pd
                filepath = session['last_upload']['filepath']
                
                if os.path.exists(filepath):
                    # Read the Excel file
                    df = pd.read_excel(filepath)
                    
                    # Convert to employee format using the correct SAP column names
                    employees = []
                    for index, row in df.iterrows():
                        # Extract employee ID from EMPLOYEECODE column
                        employee_id = str(row['EMPLOYEECODE']) if 'EMPLOYEECODE' in df.columns and pd.notna(row['EMPLOYEECODE']) else f"RW{index+1:03d}"
                        
                        # Extract name from SURNAME and FIRSTNAME columns
                        first_name = str(row['FIRSTNAME']) if 'FIRSTNAME' in df.columns and pd.notna(row['FIRSTNAME']) else ""
                        surname = str(row['SURNAME']) if 'SURNAME' in df.columns and pd.notna(row['SURNAME']) else ""
                        
                        # Extract other fields using correct SAP column names
                        grade_band = str(row['BAND']) if 'BAND' in df.columns and pd.notna(row['BAND']) else 'O-Q'
                        department = str(row['DEPARTMENT']) if 'DEPARTMENT' in df.columns and pd.notna(row['DEPARTMENT']) else 'General'
                        job_title = str(row['JOBLONG']) if 'JOBLONG' in df.columns and pd.notna(row['JOBLONG']) else 'Employee'
                        basic_salary = float(row['TPE']) if 'TPE' in df.columns and pd.notna(row['TPE']) else 0
                        ctc = float(row['CTC']) if 'CTC' in df.columns and pd.notna(row['CTC']) else 0
                        
                        # Extract access dates from Excel
                        access_granted = str(row.get('ACCESSGRANTED', session['last_upload']['upload_time'][:10])) if 'ACCESSGRANTED' in df.columns and pd.notna(row.get('ACCESSGRANTED')) else session['last_upload']['upload_time'][:10]
                        access_expires = str(row.get('ACCESSEXPIRES', '2024-12-31')) if 'ACCESSEXPIRES' in df.columns and pd.notna(row.get('ACCESSEXPIRES')) else '2024-12-31'
                        
                        # Calculate actual days remaining
                        try:
                            from datetime import datetime, date
                            expiry_date = datetime.strptime(access_expires, '%Y-%m-%d').date()
                            today = date.today()
                            days_remaining = (expiry_date - today).days
                            is_expired = days_remaining < 0
                        except:
                            days_remaining = 132
                            is_expired = False
                        
                        employee = {
                            'employee_id': employee_id,
                            'first_name': first_name,
                            'surname': surname,
                            'grade_band': grade_band,
                            'department': department,
                            'job_title': job_title,
                            'basic_salary': basic_salary,
                            'ctc': ctc,
                            'access_granted': access_granted,
                            'access_expires': access_expires,
                            'days_remaining': days_remaining,
                            'package_submitted': False,
                            'is_expired': is_expired
                        }
                        employees.append(employee)
                    
                    return employees
                    
            except Exception as e:
                logger.error(f"Error reading uploaded SAP file: {str(e)}")
                return []
        
        return []
        
    except Exception as e:
        logger.error(f"Error getting active Rand Water employees: {str(e)}")
        return []

# ============================================================================
# EMPLOYEE AND SUPER ADMIN ROUTES
# ============================================================================

# Simple employee and super admin routes added

# ============================================================================
# EMPLOYEE ROUTES
# ============================================================================

@app.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    """Employee login for Package Builder"""
    if session.get('employee_id'):
        return redirect(url_for('employee_dashboard'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple employee validation (you can enhance this)
        if username.startswith('RW') and len(username) >= 6:
            session['employee_id'] = username
            session['username'] = username
            return redirect(url_for('employee_dashboard'))
        else:
            error = "Invalid credentials or access expired"
    
    return render_template('employee_login.html', error=error, config=RANDWATER_CONFIG)

@app.route('/employee/logout')
def employee_logout():
    """Employee logout"""
    session.clear()
    return redirect(url_for('employee_login'))

@app.route('/employee/dashboard')
def employee_dashboard():
    """Employee dashboard"""
    if not session.get('employee_id'):
        return redirect(url_for('employee_login'))
    
    return render_template('employee_login.html', 
                         employee_id=session.get('employee_id'),
                         config=RANDWATER_CONFIG)

# ============================================================================
# SUPER ADMIN ROUTES
# ============================================================================

@app.route('/superadmin/login', methods=['GET', 'POST'])
def super_admin_login():
    """Super Admin login for system configuration"""
    if session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_dashboard'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Super admin credentials
        if username == 'SuperAdmin' and password == 'SmartHR2024!SuperAdmin':
            session['isSuperAdmin'] = True
            session['superadmin_username'] = username
            return redirect(url_for('super_admin_dashboard'))
        else:
            error = "Invalid super admin credentials"
    
    return render_template('super_admin_login.html', error=error, config=RANDWATER_CONFIG)

@app.route('/superadmin/logout')
def super_admin_logout():
    """Super Admin logout"""
    session.pop('isSuperAdmin', None)
    session.pop('superadmin_username', None)
    return redirect(url_for('superadmin_login'))

@app.route('/superadmin/dashboard')
def super_admin_dashboard():
    """Super Admin dashboard for system configuration"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('superadmin_login'))
    
    stats = {
        'total_randwater_admins': 3,
        'total_employees': 150,  # Placeholder
        'total_packages': 45,    # Placeholder
        'system_version': '2.0.0'
    }
    
    return render_template('super_admin_dashboard.html',
                          stats=stats,
                          config=RANDWATER_CONFIG)

# ============================================================================
# RAND WATER ADMIN ROUTES
# ============================================================================

@app.route('/admin/randwater', methods=['GET', 'POST'])
def randwater_admin_login():
    """Randwater admin login"""
    if session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_panel'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Rand Water admin authentication
        if username == 'RandWaterAdmin' and password == 'RandWater2024!':
            session['admin'] = True
            session['isRandWaterAdmin'] = True
            return redirect(url_for('randwater_admin_panel'))
        else:
            error = "Incorrect Rand Water admin credentials"
    
    return render_template('randwater_admin_login.html', error=error, config=RANDWATER_CONFIG)

@app.route('/admin/randwater/dashboard')
def randwater_admin_panel():
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    settings = load_tax_settings()
    packages = get_all_randwater_completed_packages()
    
    total_packages = len(packages)
    completed_packages = len([p for p in packages if p.get('status') == 'COMPLETED'])
    pending_packages = len([p for p in packages if p.get('status') == 'PENDING'])
    
    # Calculate completion rate safely
    completion_rate = 0.0
    if total_packages > 0:
        completion_rate = (completed_packages / total_packages) * 100
    
    # Get active employees from uploaded SAP data
    active_employees = get_active_randwater_employees()
    total_employees = len(active_employees)
    
    stats = {
        'total_packages': total_packages,
        'completed_packages': completed_packages,
        'pending_submissions': pending_packages,  # Added pending count
        'submitted_packages': completed_packages,   # Fixed: template expects submitted_packages
        'completion_rate': completion_rate,
        'total_employees': total_employees,
        'company': 'RANDWATER'
    }
    
    return render_template('randwater_admin_panel_enhanced.html', settings=settings, stats=stats, active_employees=active_employees, config=RANDWATER_CONFIG)

# ============================================================================
# SUPER ADMIN ADDITIONAL ROUTES
# ============================================================================

@app.route('/calculation_tables')
def calculation_tables():
    """Super Admin - Manage calculation tables and parameters"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    return render_template('calculation_tables.html', config=RANDWATER_CONFIG)

@app.route('/user_management')
def user_management():
    """Super Admin - User management interface"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    return render_template('user_management.html', config=RANDWATER_CONFIG)

@app.route('/security_settings')
def security_settings():
    """Super Admin - Security settings interface"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    return render_template('security_settings.html', config=RANDWATER_CONFIG)

@app.route('/email_logs')
def email_logs():
    """Super Admin - Email logs and audit trail"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    return render_template('email_logs.html', config=RANDWATER_CONFIG)

@app.route('/smtp_config_management')
def smtp_config_management():
    """Super Admin - SMTP configuration management"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    return render_template('smtp_config.html', config=RANDWATER_CONFIG)

# ============================================================================
# RAND WATER ADMIN ENHANCED FUNCTIONALITY
# ============================================================================

@app.route('/upload_sap_data')
def upload_sap_data():
    """Rand Water Admin - SAP data upload interface"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    return render_template('upload_sap_data.html', config=RANDWATER_CONFIG)

@app.route('/upload_sap_data', methods=['POST'])
def upload_sap_data_post():
    """Rand Water Admin - Handle SAP data upload"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        if 'sap_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['sap_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename.endswith('.xlsx'):
            # Save uploaded file
            filename = f"randwater_sap_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join('uploads', filename)
            os.makedirs('uploads', exist_ok=True)
            file.save(filepath)
            
            # Store upload info in session
            session['last_upload'] = {
                'filename': filename,
                'filepath': filepath,
                'upload_time': datetime.now().isoformat()
            }
            
            return jsonify({'success': True, 'filename': filename})
        else:
            return jsonify({'error': 'Invalid file type. Please upload Excel (.xlsx) files only'}), 400
            
    except Exception as e:
        logger.error(f"Error uploading SAP data: {str(e)}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/admin/randwater/clear-uploaded-data', methods=['POST'])
def clear_uploaded_data():
    """Rand Water Admin - Clear uploaded SAP data"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Clear session data
        session.pop('last_upload', None)
        
        # Optionally delete uploaded files
        uploads_dir = 'uploads'
        if os.path.exists(uploads_dir):
            for file in os.listdir(uploads_dir):
                if file.startswith('randwater_sap_data_'):
                    os.remove(os.path.join(uploads_dir, file))
        
        return jsonify({'success': True, 'message': 'Uploaded data cleared'})
        
    except Exception as e:
        logger.error(f"Error clearing uploaded data: {str(e)}")
        return jsonify({'error': 'Failed to clear data'}), 500

@app.route('/manage_employee_access')
def manage_employee_access():
    """Rand Water Admin - Employee access management"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    # Get active employees and calculate stats
    active_employees = get_active_randwater_employees()
    total_employees = len(active_employees)
    
    # Calculate access statistics
    active_access = len([e for e in active_employees if not e.get('is_expired', False)])
    expired_access = len([e for e in active_employees if e.get('is_expired', False)])
    pending_submissions = len([e for e in active_employees if not e.get('package_submitted', False)])
    
    stats = {
        'total_employees': total_employees,
        'active_access': active_access,
        'expired_access': expired_access,
        'pending_submissions': pending_submissions
    }
    
    return render_template('manage_employee_access.html', 
                         config=RANDWATER_CONFIG, 
                         stats=stats,
                         active_employees=active_employees)

@app.route('/manage_packages')
def manage_packages():
    """Rand Water Admin - Package management interface"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    return render_template('manage_packages.html', config=RANDWATER_CONFIG)

@app.route('/export_packages_for_sap')
def export_packages_for_sap():
    """Rand Water Admin - Export packages for SAP"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    return render_template('package_analytics.html', config=RANDWATER_CONFIG)

@app.route('/package_analytics')
def package_analytics():
    """Rand Water Admin - Package analytics and reporting"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    return render_template('package_analytics.html', config=RANDWATER_CONFIG)

@app.route('/admin/randwater/employee-details/<employee_id>')
def employee_details(employee_id):
    """Rand Water Admin - Get employee details for modal"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401

    # Mock data for now - you can enhance this with real data
    employee_data = {
        'employee': {
            'employee_id': employee_id,
            'username': f'RW{employee_id}',
            'grade_band': 'O-Q',
            'status': 'ACTIVE',
            'access_granted': '2024-08-21T00:00:00',
            'access_expires': '2024-12-31T23:59:59'
        },
        'package': {
            'basic_salary': 25000,
            'total_earnings': 35000,
            'total_deductions': 8000,
            'net_pay': 27000,
            'ctc': 45000
        }
    }

    return jsonify(employee_data)

@app.route('/admin/randwater/employee-payslip/<employee_id>')
def employee_payslip(employee_id):
    """Rand Water Admin - Get employee payslip data from uploaded SAP file"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401

    def safe_float(value, default=0.0):
        """Safely convert value to float, handling text values like 'Yes', 'No'"""
        if pd.isna(value) or value is None:
            return default
        try:
            # Handle text values that should be numeric
            if isinstance(value, str):
                value = value.strip().upper()
                if value in ['YES', 'NO', 'N/A', '']:
                    return default
                # Try to convert to float
                return float(value)
            return float(value)
        except (ValueError, TypeError):
            return default

    try:
        # Check if we have uploaded SAP data
        if not session.get('last_upload'):
            return jsonify({'error': 'No SAP data uploaded. Please upload employee data first.'}), 400
        
        # Read the uploaded Excel file to get actual employee data
        import pandas as pd
        filepath = session['last_upload']['filepath']
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Uploaded file not found. Please re-upload SAP data.'}), 400
        
        # Read the Excel file
        df = pd.read_excel(filepath)
        
        # Find the employee in the uploaded data
        employee_row = None
        for index, row in df.iterrows():
            if 'EMPLOYEECODE' in df.columns and str(row['EMPLOYEECODE']) == str(employee_id):
                employee_row = row
                break
        
        if employee_row is None:
            return jsonify({'error': f'Employee {employee_id} not found in uploaded SAP data'}), 404
        
        # Extract actual values from the Excel file using the correct column names
        payslip_data = {
            'success': True,
            'employee': {
                'employee_id': str(employee_row['EMPLOYEECODE']) if 'EMPLOYEECODE' in df.columns else employee_id,
                'first_name': str(employee_row['FIRSTNAME']) if 'FIRSTNAME' in df.columns else '',
                'surname': str(employee_row['SURNAME']) if 'SURNAME' in df.columns else '',
                'grade_band': str(employee_row['BAND']) if 'BAND' in df.columns else 'O-Q',
                'department': str(employee_row['DEPARTMENT']) if 'DEPARTMENT' in df.columns else 'General',
                'job_title': str(employee_row['JOBLONG']) if 'JOBLONG' in df.columns else 'Employee',
                'basic_salary': safe_float(employee_row.get('TPE', 0)),
                'ctc': safe_float(employee_row.get('CTC', 0))
            },
            'payslip': {
                'basic_salary': safe_float(employee_row.get('TPE', 0)),
                'car_allowance': safe_float(employee_row.get('CAR', 0)),
                'cellphone_allowance': safe_float(employee_row.get('CELLPHONEALLOWANCE', 0)),
                'data_service_allowance': safe_float(employee_row.get('DATASERVICEALLOWANCE', 0)),
                'housing_allowance': safe_float(employee_row.get('HOUSING', 0)),
                'pension': safe_float(employee_row.get('pension', 0)),
                'medical_aid': safe_float(employee_row.get('MEDICAL', 0)),
                'bonus': safe_float(employee_row.get('BONUSPROVISION', 0)),
                'critical_skills': safe_float(employee_row.get('CRITICALSKILLS', 0)),
                'cash_allowance': safe_float(employee_row.get('CASH', 0))
            }
        }
        
        # Calculate bonus provision (monthly amount deducted from package)
        bonus_provision_monthly = payslip_data['payslip']['bonus'] / 12 if payslip_data['payslip']['bonus'] > 0 else 0
        
        # Calculate employer contributions (excluding UIF and SDL)
        # These would come from Excel columns like EMPLOYERPENSION, EMPLOYERMEDICAL, etc.
        employer_pension = safe_float(employee_row.get('EMPLOYERPENSION', 0))
        employer_medical = safe_float(employee_row.get('EMPLOYERMEDICAL', 0))
        employer_other = safe_float(employee_row.get('EMPLOYEROTHER', 0))
        
        total_employer_contributions = employer_pension + employer_medical + employer_other
        
        # Calculate total earnings (excluding bonus provision - it's not paid monthly)
        payslip_data['payslip']['total_earnings'] = (
            payslip_data['payslip']['basic_salary'] +
            payslip_data['payslip']['car_allowance'] +
            payslip_data['payslip']['cellphone_allowance'] +
            payslip_data['payslip']['data_service_allowance'] +
            payslip_data['payslip']['housing_allowance'] +
            payslip_data['payslip']['critical_skills'] +
            payslip_data['payslip']['cash_allowance']
            # Note: bonus is NOT included in monthly earnings
        )
        
        # Calculate UIF (1% of basic salary, capped at R177.12 per month)
        uif_rate = 0.01  # 1%
        uif_amount = min(payslip_data['payslip']['basic_salary'] * uif_rate, 177.12)
        payslip_data['payslip']['uif'] = round(uif_amount, 2)
        
        # Calculate tax using the COMPLETE tax calculation system from your existing code
        settings = load_tax_settings()
        
        # Get age and medical info (you can extract these from Excel if available)
        age = 35  # Default age - you can extract from Excel data if available
        has_medical = payslip_data['payslip']['medical_aid'] > 0
        dependants = 0  # This could be extracted from Excel data if available
        
        # Calculate taxable income (including travel allowance rules)
        travel_allowance = payslip_data['payslip'].get('car_allowance', 0)
        annual_travel_taxable = travel_allowance * 12 * 0.8  # 80% of travel allowance is taxable
        gross_excluding_travel = payslip_data['payslip']['total_earnings'] - travel_allowance
        taxable_income = gross_excluding_travel * 12 + annual_travel_taxable
        
        # Calculate pension deductions (capped at 27.5% of taxable income or R350,000)
        pension_employee = payslip_data['payslip'].get('pension', 0)
        total_pension_deductible = (pension_employee + employer_pension) * 12
        total_pension_deductible = min(total_pension_deductible, 0.275 * taxable_income, 350000)
        
        taxable_income -= total_pension_deductible
        
        # PAYE calculation using SARS brackets
        annual_tax = calculate_tax(taxable_income, settings)
        
        # Apply age-based rebates
        rebate = settings.get('rebate_primary', 17235)
        if age >= 65:
            rebate += settings.get('rebate_secondary', 9444)
        if age >= 75:
            rebate += settings.get('rebate_tertiary', 3145)
        
        annual_tax -= rebate
        annual_tax = max(0, annual_tax)
        
        # Medical tax credits (complete logic from your existing system)
        if has_medical:
            credit = settings.get('medical_main', 364)
            if dependants >= 1:
                credit += settings.get('medical_first', 364)
            if dependants > 1:
                credit += (dependants - 1) * settings.get('medical_additional', 246)
            annual_tax -= credit * 12
        
        annual_tax = max(0, annual_tax)
        monthly_tax = round(annual_tax / 12, 2)
        payslip_data['payslip']['tax'] = monthly_tax
        
        # Calculate bonus tax provision (monthly tax on bonus)
        if payslip_data['payslip']['bonus'] > 0:
            # Calculate tax on annual bonus using marginal rate
            bonus_tax_rate = 0.31  # Default marginal rate - you can calculate this more precisely
            bonus_tax_monthly = (payslip_data['payslip']['bonus'] * bonus_tax_rate) / 12
            payslip_data['payslip']['bonus_tax_provision'] = round(bonus_tax_monthly, 2)
        else:
            payslip_data['payslip']['bonus_tax_provision'] = 0
        
        # Calculate total deductions including UIF, tax, and bonus tax provision
        total_deductions = (
            payslip_data['payslip']['pension'] + 
            payslip_data['payslip']['medical_aid'] + 
            payslip_data['payslip']['uif'] + 
            payslip_data['payslip']['tax'] +
            payslip_data['payslip']['bonus_tax_provision']
        )
        payslip_data['payslip']['total_deductions'] = round(total_deductions, 2)
        
        # Calculate net pay
        payslip_data['payslip']['net_pay'] = payslip_data['payslip']['total_earnings'] - total_deductions
        
        # Add package breakdown information
        payslip_data['payslip']['package_breakdown'] = {
            'tctc_monthly': payslip_data['employee']['ctc'],
            'bonus_provision_monthly': round(bonus_provision_monthly, 2),
            'basic_salary_after_bonus': round(payslip_data['employee']['ctc'] - bonus_provision_monthly, 2),
            'employer_contributions': round(total_employer_contributions, 2),
            'other_earnings': round(payslip_data['payslip']['total_earnings'] - payslip_data['payslip']['basic_salary'], 2)
        }
        
        return jsonify(payslip_data)
        
    except Exception as e:
        logger.error(f"Error getting employee payslip: {str(e)}")
        return jsonify({'error': f'Failed to load payslip data: {str(e)}'}), 500

@app.route('/salary_simulator')
def salary_simulator():
    """Rand Water Admin - Salary simulator interface"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    return render_template('salary_simulator.html', config=RANDWATER_CONFIG)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 