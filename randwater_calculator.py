from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, g, flash
import json
import math
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import requests
import os
from datetime import datetime, timedelta
import logging
import csv
from typing import Dict, List, Optional
from models import PackageManager
import smtplib
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import re
from typing import Dict, List, Optional, Tuple

app = Flask(__name__)
app.secret_key = 'randwater-super-secret-key-2024'  # Change this in production

# Disable template caching in development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# ============================================================================
# PASSWORD POLICY ENFORCEMENT
# ============================================================================

def load_password_policy():
    """Load password policy settings from system backup or defaults"""
    try:
        # Try to load from system backup
        backup_files = [f for f in os.listdir('.') if f.startswith('backups/system_backup_') and f.endswith('.json')]
        if backup_files:
            latest_backup = max(backup_files)
            with open(latest_backup, 'r') as f:
                backup_data = json.load(f)
                if 'security_settings' in backup_data and 'password_policy' in backup_data['security_settings']:
                    return backup_data['security_settings']['password_policy']
    except:
        pass
    
    # Default password policy
    return {
        'min_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_numbers': True,
        'require_special': True,
        'max_age_days': 90,
        'password_history': 5
    }

def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password against policy requirements
    Returns: (is_valid, list_of_errors)
    """
    policy = load_password_policy()
    errors = []
    
    # Check minimum length
    if len(password) < policy['min_length']:
        errors.append(f"Password must be at least {policy['min_length']} characters long")
    
    # Check uppercase requirement
    if policy['require_uppercase'] and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Check lowercase requirement
    if policy['require_lowercase'] and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Check numbers requirement
    if policy['require_numbers'] and not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one number")
    
    # Check special characters requirement
    if policy['require_special'] and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        errors.append("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;':\",./<>?)")
    
    # Check for common weak patterns
    if password.lower() in ['password', '123456', 'qwerty', 'admin', 'letmein', 'welcome']:
        errors.append("Password cannot be a common weak password")
    
    # Check for repeated characters
    if re.search(r'(.)\1{2,}', password):
        errors.append("Password cannot contain more than 2 consecutive identical characters")
    
    return len(errors) == 0, errors

def check_password_history(user_id: int, new_password: str) -> bool:
    """
    Check if new password is in password history
    Returns True if password is acceptable (not in history)
    """
    policy = load_password_policy()
    history_count = policy.get('password_history', 5)
    
    if history_count == 0:
        return True
    
    try:
        # Load password history (stored in system_users.json)
        system_users = load_system_users()
        user = next((u for u in system_users if u['id'] == user_id), None)
        
        if not user:
            return True
        
        # Check against password history
        password_history = user.get('password_history', [])
        for old_password_hash in password_history:
            if check_password_hash(old_password_hash, new_password):
                return False
        
        return True
    except:
        return True

def check_password_expiry(user_id: int) -> Tuple[bool, str]:
    """
    Check if user's password has expired
    Returns: (is_expired, days_remaining_or_expired_message)
    """
    policy = load_password_policy()
    max_age_days = policy.get('max_age_days', 90)
    
    try:
        system_users = load_system_users()
        user = next((u for u in system_users if u['id'] == user_id), None)
        
        if not user:
            return False, "User not found"
        
        last_password_change = user.get('password_changed_date')
        if not last_password_change:
            return False, "Password change date not recorded"
        
        # Parse the date
        try:
            change_date = datetime.strptime(last_password_change, '%Y-%m-%d %H:%M:%S')
            days_since_change = (datetime.now() - change_date).days
            
            if days_since_change >= max_age_days:
                return True, f"Password expired {days_since_change - max_age_days} days ago"
            else:
                days_remaining = max_age_days - days_since_change
                return False, f"{days_remaining} days remaining"
        except:
            return False, "Invalid password change date format"
    
    except:
        return False, "Error checking password expiry"

def update_password_history(user_id: int, old_password_hash: str):
    """Update password history for a user"""
    policy = load_password_policy()
    history_count = policy.get('password_history', 5)
    
    if history_count == 0:
        return
    
    try:
        system_users = load_system_users()
        user = next((u for u in system_users if u['id'] == user_id), None)
        
        if not user:
            return
        
        # Add old password to history
        password_history = user.get('password_history', [])
        password_history.insert(0, old_password_hash)  # Add to beginning
        
        # Keep only the required number of passwords
        password_history = password_history[:history_count]
        
        # Update user record
        user['password_history'] = password_history
        user['password_changed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save updated users
        save_system_users(system_users)
    except Exception as e:
        logger.error(f"Error updating password history: {e}")

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
    },
    'smtp': {
        'host': os.environ.get('SMTP_HOST', 'smtp.gosmarthr.com'),
        'port': int(os.environ.get('SMTP_PORT', '587')),
        'username': os.environ.get('SMTP_USERNAME', 'smartie@gosmarthr.com'),
        'password': os.environ.get('SMTP_PASSWORD', '$m@rtHR2023!'),
        'from_address': os.environ.get('SMTP_FROM', 'smartie@gosmarthr.com'),
        'use_tls': True
    },
    'app_base_url': os.environ.get('APP_BASE_URL', 'http://localhost:5001')
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tax settings file for Rand Water
TAX_SETTINGS_FILE = 'randwater_tax_settings.json'

# Initialize persistent storage for uploads
package_builder = PackageManager()

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
    return redirect(url_for('unified_login'))

@app.route('/calculator')
def randwater_calculator():
    """Rand Water specific calculator view"""
    return render_template('randwater_calculator.html', config=RANDWATER_CONFIG)

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

@app.route('/api/randwater/employee/<employee_id>')
def get_randwater_employee_data(employee_id):
    """Get Rand Water employee data from SAP uploads"""
    try:
        from models import PackageManager
        package_manager = PackageManager()
        
        # Get SAP data for the employee
        sap_data = package_manager.get_sap_data_for_employee(employee_id)
        
        if not sap_data:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Format the data for the frontend
        response_data = {
            'employee_id': employee_id,
            'first_name': sap_data.get('FIRSTNAME', ''),
            'surname': sap_data.get('SURNAME', ''),
            'email': f"{sap_data.get('FIRSTNAME', '').lower()}.{sap_data.get('SURNAME', '').lower()}@randwater.co.za",
            'job_title': sap_data.get('JOBLONG', ''),
            'department': sap_data.get('DEPARTMENT', ''),
            'basic_salary': sap_data.get('TPE', 0),  # Basic salary (non-allowance)
            'ctc': 0,  # Will be calculated
            'allowances': [
                {'name': 'Car Allowance', 'amount': sap_data.get('CAR', 0), 'type': 'car_allowance'},
                {'name': 'Cash Component', 'amount': sap_data.get('CASH', 0), 'type': 'cash_component'},
                {'name': 'Housing Allowance', 'amount': sap_data.get('HOUSING', 0), 'type': 'housing_allowance'},
                {'name': 'Cellphone Allowance', 'amount': sap_data.get('CELLPHONEALLOWANCE', 0), 'type': 'cellphone_allowance'},
                {'name': 'Data Service Allowance', 'amount': sap_data.get('DATASERVICEALLOWANCE', 0), 'type': 'data_service_allowance'},
                {'name': 'Critical Skills', 'amount': sap_data.get('CRITICALSKILLS', 0), 'type': 'critical_skills'}
            ],
            'deductions': [
                {'name': 'Pension/Provident Employee', 'amount': sap_data.get('PENSIONEECONTRIBUTION', 0)},
                {'name': 'Medical Aid Employee', 'amount': sap_data.get('MEDICAL', 0)},
                {'name': 'Group Life Employee', 'amount': sap_data.get('GROUPLIFEEECONTRIBUTION', 0)}
            ],
            'employer_contributions': [
                {'name': 'Pension/Provident Employer', 'amount': sap_data.get('PENSIONERCONTRIBUTION', 0)},
                {'name': 'UIF Employer', 'amount': sap_data.get('UIF', 0)}
            ],
            'randwater_benefits': []
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting employee data: {str(e)}")
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

        # Get basic salary separately (not part of gross allowances)
        basic_salary = float(form.get("basic_salary", 0))
        
        # Calculate gross earnings from ALLOWANCES ONLY (exclude basic salary)
        # Gross = Car Allowance + Cash Component + Housing Allowance + Cellphone Allowance + Data Service Allowance + Critical Skills
        gross_allowances = sum(val for label, val in earnings)
        
        total_deductions = sum(val for label, val in deductions)
        total_employer = sum(val for label, val in employer)
        total_randwater_benefits = sum(val for label, val in randwater_benefits)

        # Rand Water specific UIF calculation - based on total earnings (basic salary + allowances)
        total_earnings = basic_salary + gross_allowances
        uif_cap = settings.get('uif_ceiling', 17712)
        uif = min(uif_cap, total_earnings * 0.01)
        
        # Get age and medical info
        age = int(form.get("age", 0))
        has_medical = form.get("has_medical", "no") == "yes"
        dependants = int(form.get("dependants", 0))

        # Calculate taxable income (including travel allowance)
        travel_allowance = next((val for label, val in earnings if 'transport' in label.lower()), 0)
        annual_travel_taxable = travel_allowance * 12 * 0.8
        # For tax purposes, use total earnings (basic salary + allowances) excluding travel allowance
        gross_excluding_travel = total_earnings - travel_allowance
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

        # Net pay calculation: Total earnings (basic salary + allowances) - total deductions
        net_pay = total_earnings - total_deductions

        return jsonify({
            "basic_salary": basic_salary,
            "gross_allowances": gross_allowances,  # Only allowances for tax base
            "total_earnings": total_earnings,  # Basic salary + allowances for display
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

def get_employee_fixed_ctc(employee_id):
    """Get the fixed CTC for an employee from original SAP data"""
    try:
        if package_builder.sap_uploads:
            recent_uploads = package_builder.sap_uploads
            recent_uploads.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
            latest_upload = recent_uploads[0]
            
            if 'employee_data' in latest_upload:
                for emp_data in latest_upload['employee_data']:
                    if str(emp_data.get('EMPLOYEECODE', '')) == str(employee_id):
                        # Return the original CTC from SAP
                        return float(emp_data.get('CTC', emp_data.get('TCTC', 0)))
        return None
    except Exception as e:
        logger.error(f"Error getting fixed CTC: {str(e)}")
        return None

def validate_package_changes(current_package, changes, fixed_ctc):
    """Validate and auto-adjust package changes for CTC reallocation"""
    try:
        # Get fixed components that cannot be changed
        housing_allowance = float(current_package.get('housing_allowance', 0))
        transport_allowance = float(current_package.get('transport_allowance', 0))
        cellphone_allowance = float(current_package.get('cellphone_allowance', 0))
        data_service_allowance = float(current_package.get('data_service_allowance', 0))
        medical_aid = float(current_package.get('medical_aid', 0))
        
        # Get variable components from changes or current values
        car_allowance = float(changes.get('car_allowance', current_package.get('car_allowance', 0)))
        bonus_annual = float(changes.get('bonus', current_package.get('bonus', 0)))
        
        # Convert 13th cheque to monthly portion
        bonus_monthly = bonus_annual / 12
        
        # Calculate fixed allocations
        fixed_components = (housing_allowance + transport_allowance + 
                          cellphone_allowance + data_service_allowance + 
                          medical_aid + car_allowance + bonus_monthly)
        
        # Calculate remaining budget for basic salary
        remaining_for_basic = fixed_ctc - fixed_components
        
        # Auto-adjust basic salary to fit within CTC
        if remaining_for_basic < 0:
            return {
                'valid': False,
                'error': f'Car allowance and bonus exceed available budget. Available: R{fixed_ctc - (fixed_components - car_allowance - bonus_monthly):.2f}'
            }
        
        # Update changes with calculated basic salary
        changes['basic_salary'] = remaining_for_basic
        changes['bonus'] = bonus_monthly  # Store monthly portion
        
        # Validation warnings
        warnings = []
        basic_percentage = (remaining_for_basic / fixed_ctc) * 100
        car_percentage = (car_allowance / fixed_ctc) * 100
        bonus_percentage = (bonus_annual / fixed_ctc) * 100
        
        if basic_percentage < 50:
            warnings.append(f"Basic salary auto-adjusted to {basic_percentage:.1f}% of CTC (below typical 50%)")
        elif basic_percentage > 70:
            warnings.append(f"Basic salary auto-adjusted to {basic_percentage:.1f}% of CTC (above typical 70%)")
        
        if car_allowance > 0 and car_percentage < 30:
            warnings.append(f"Car allowance is {car_percentage:.1f}% of CTC (below 30% minimum for O to Q band)")
        
        if bonus_percentage < 10:
            warnings.append(f"Annual bonus is {bonus_percentage:.1f}% of CTC (below 10% minimum)")
        elif bonus_percentage > 70:
            warnings.append(f"Annual bonus is {bonus_percentage:.1f}% of CTC (above 70% maximum)")
        
        return {'valid': True, 'warnings': warnings, 'auto_adjustments': changes}
        
    except Exception as e:
        logger.error(f"Error validating changes: {str(e)}")
        return {'valid': False, 'error': 'Validation error'}

def calculate_employee_deductions(package_data):
    """Calculate tax and UIF deductions for an employee package"""
    try:
        # Load tax settings
        settings = load_tax_settings()
        
        # Get package components
        basic_salary = float(package_data.get('basic_salary', 0))
        car_allowance = float(package_data.get('car_allowance', 0))
        housing_allowance = float(package_data.get('housing_allowance', 0))
        transport_allowance = float(package_data.get('transport_allowance', 0))
        cellphone_allowance = float(package_data.get('cellphone_allowance', 0))
        data_service_allowance = float(package_data.get('data_service_allowance', 0))
        bonus_monthly = float(package_data.get('bonus', 0))  # This should be monthly portion
        
        # Calculate gross monthly income for UIF (all income components)
        gross_monthly_for_uif = (basic_salary + car_allowance + housing_allowance + 
                               transport_allowance + cellphone_allowance + data_service_allowance + bonus_monthly)
        
        # Calculate taxable income (basic salary + car allowance for tax purposes)
        taxable_monthly = basic_salary + car_allowance
        annual_taxable = taxable_monthly * 12
        
        # Pension contribution (on basic salary only)
        pension_rate = 0.075  # 7.5%
        pension_monthly = basic_salary * pension_rate
        annual_pension = pension_monthly * 12
        
        # Taxable income after pension deduction
        annual_taxable_after_pension = annual_taxable - annual_pension
        
        # Calculate PAYE tax
        annual_tax = calculate_tax(annual_taxable_after_pension, settings)
        
        # Apply primary rebate
        rebate = settings.get('rebate_primary', 17235)
        annual_tax = max(0, annual_tax - rebate)
        
        # Monthly tax
        monthly_tax = annual_tax / 12
        
        # UIF calculation (1% of ALL gross income, capped at R177.12 per month)
        uif_contribution = min(gross_monthly_for_uif * 0.01, 177.12)
        
        # Total deductions
        medical_aid = float(package_data.get('medical_aid', 0))
        total_deductions = monthly_tax + uif_contribution + medical_aid + pension_monthly
        
        logger.info(f"Tax calculation: Basic={basic_salary}, Car={car_allowance}, Taxable={taxable_monthly}, Tax={monthly_tax:.2f}")
        logger.info(f"UIF calculation: Gross={gross_monthly_for_uif}, UIF={uif_contribution:.2f}")
        
        return {
            'paye_tax': round(monthly_tax, 2),
            'uif_contribution': round(uif_contribution, 2),
            'pension_fund': round(pension_monthly, 2),
            'total_deductions': round(total_deductions, 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating deductions: {str(e)}")
        return {
            'paye_tax': 0,
            'uif_contribution': 0,
            'pension_fund': 0,
            'total_deductions': 0
        }

def load_tax_settings():
    """Load tax settings from file"""
    try:
        with open('tax_settings.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load tax settings: {str(e)}")
        # Return default tax settings
        return {
            "tax_brackets": [
                {"min": 0, "max": 237100, "rate": 0.18, "cumulative": 0},
                {"min": 237101, "max": 370500, "rate": 0.26, "cumulative": 42678},
                {"min": 370501, "max": 512800, "rate": 0.31, "cumulative": 77362},
                {"min": 512801, "max": 673000, "rate": 0.36, "cumulative": 121475},
                {"min": 673001, "max": 857900, "rate": 0.39, "cumulative": 179147},
                {"min": 857901, "max": 1817000, "rate": 0.41, "cumulative": 251258},
                {"min": 1817001, "max": float('inf'), "rate": 0.45, "cumulative": 644489}
            ],
            "rebate_primary": 17235,
            "rebate_secondary": 9444,
            "rebate_tertiary": 3145,
            "medical_credits_limit": 332,
            "uif_ceiling": 177.12
        }

def calculate_tax(annual_taxable_income, tax_settings):
    """Calculate annual tax using tax brackets"""
    try:
        tax_brackets = tax_settings.get('tax_brackets', [])
        
        for bracket in tax_brackets:
            if annual_taxable_income <= bracket['max']:
                # Tax = cumulative + (excess * rate)
                excess = annual_taxable_income - bracket['min']
                tax = bracket['cumulative'] + (excess * bracket['rate'])
                return max(0, tax)
        
        # If we get here, use the highest bracket
        if tax_brackets:
            highest_bracket = tax_brackets[-1]
            excess = annual_taxable_income - highest_bracket['min']
            tax = highest_bracket['cumulative'] + (excess * highest_bracket['rate'])
            return max(0, tax)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error calculating tax: {str(e)}")
        return 0

def get_employee_package_data(employee_id):
    """Get current employee package data for calculations"""
    try:
        # Get the latest SAP upload data
        if package_builder.sap_uploads:
            recent_uploads = package_builder.sap_uploads
            recent_uploads.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
            latest_upload = recent_uploads[0]
            
            if 'employee_data' in latest_upload:
                for emp_data in latest_upload['employee_data']:
                    if str(emp_data.get('EMPLOYEECODE', '')) == str(employee_id):
                        # Convert SAP data to package format
                        return {
                            'basic_salary': float(emp_data.get('TPE', 0)),
                            'car_allowance': float(emp_data.get('CAR', 0)),
                            'medical_aid': float(emp_data.get('MEDICAL', 0)),
                            'housing_allowance': float(emp_data.get('HOUSING', 0)),
                            'transport_allowance': float(emp_data.get('TRANSPORT', 0)),
                            'bonus': float(emp_data.get('BONUSPROVISION', 0)),
                            'pension_fund': float(emp_data.get('PENSIONCONTRIBUTIONFUND', 0)),
                            'paye_tax': float(emp_data.get('PAYETAX', 0)),
                            'uif_contribution': float(emp_data.get('UIF', 0)),
                            'total_deductions': float(emp_data.get('TOTALDEDUCTIONS', 0))
                        }
        return None
    except Exception as e:
        logger.error(f"Error getting employee package data: {str(e)}")
        return None

def calculate_employee_deductions(package_data):
    """Calculate tax, UIF and total deductions for updated package"""
    try:
        settings = load_tax_settings()
        
        # Get package components
        basic_salary = float(package_data.get('basic_salary', 0))
        housing_allowance = float(package_data.get('housing_allowance', 0))
        transport_allowance = float(package_data.get('transport_allowance', 0))
        car_allowance = float(package_data.get('car_allowance', 0))
        bonus = float(package_data.get('bonus', 0))
        
        # Calculate gross monthly income
        gross_monthly = (basic_salary + housing_allowance + transport_allowance + 
                        car_allowance + bonus)
        
        # Calculate annual taxable income
        annual_gross = gross_monthly * 12
        
        # Apply transport allowance tax rule (80% taxable)
        transport_taxable = transport_allowance * 12 * 0.8
        annual_taxable = (annual_gross - (transport_allowance * 12)) + transport_taxable
        
        # Calculate pension deduction (max 27.5% of taxable income)
        pension_deduction = float(package_data.get('pension_fund', 0)) * 12
        max_pension_deduction = min(pension_deduction, 0.275 * annual_taxable, 350000)
        annual_taxable_after_pension = annual_taxable - max_pension_deduction
        
        # Calculate annual tax
        annual_tax = calculate_tax(annual_taxable_after_pension, settings)
        
        # Apply rebates
        rebate = settings.get('rebate_primary', 17235)
        annual_tax = max(0, annual_tax - rebate)
        
        # Monthly tax
        monthly_tax = annual_tax / 12
        
        # UIF calculation (1% of gross, capped at R177.12 per month)
        uif_cap = 177.12  # Fixed cap as per rules
        uif_contribution = min(gross_monthly * 0.01, uif_cap)
        
        # Total deductions
        medical_aid = float(package_data.get('medical_aid', 0))
        pension_monthly = float(package_data.get('pension_fund', 0))
        total_deductions = monthly_tax + uif_contribution + medical_aid + pension_monthly
        
        return {
            'paye_tax': round(monthly_tax, 2),
            'uif_contribution': round(uif_contribution, 2),
            'total_deductions': round(total_deductions, 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating deductions: {str(e)}")
        return {
            'paye_tax': 0,
            'uif_contribution': 0,
            'total_deductions': 0
        }

def get_package_audit_trail(employee_id):
    """Get audit trail for package changes"""
    try:
        audit_file = 'randwater_package_audit.json'
        if os.path.exists(audit_file):
            with open(audit_file, 'r') as f:
                all_audits = json.load(f)
                return all_audits.get(employee_id, [])
        return []
    except Exception as e:
        logger.error(f"Error loading audit trail for {employee_id}: {str(e)}")
        return []

def save_package_changes(employee_id, changes, admin_user):
    """Save package changes with CTC reallocation and validation"""
    try:
        # Get current employee package for comparison
        current_package = get_employee_package_data(employee_id)
        if not current_package:
            return {'success': False, 'error': 'Employee package not found'}
        
        # Get fixed CTC from original SAP data
        fixed_ctc = get_employee_fixed_ctc(employee_id)
        if not fixed_ctc:
            return {'success': False, 'error': 'Could not determine employee CTC'}
        
        # Validate changes against rules
        validation_result = validate_package_changes(current_package, changes, fixed_ctc)
        if not validation_result['valid']:
            return {'success': False, 'error': validation_result['error']}
        
        # Create clean audit entries for only changed fields
        audit_entries = []
        warnings = []
        
        for field_name, new_value in changes.items():
            current_value = current_package.get(field_name, 0)
            if str(current_value) != str(new_value):
                audit_entries.append({
            'timestamp': datetime.now().isoformat(),
            'admin_user': admin_user,
                    'field_name': field_name,
                    'old_value': current_value,
                    'new_value': new_value,
                    'action': 'field_update'
                })
        
        # Load existing audit trail
        audit_file = 'randwater_package_audit.json'
        if os.path.exists(audit_file):
            with open(audit_file, 'r') as f:
                all_audits = json.load(f)
        else:
            all_audits = {}
        
        # Add audit entries
        if employee_id not in all_audits:
            all_audits[employee_id] = []
        all_audits[employee_id].extend(audit_entries)
        
        # Apply changes with CTC budget constraints
        updated_package = current_package.copy()
        
        # Handle the validation and auto-adjustment from frontend
        validation_result = validate_package_changes(current_package, changes, fixed_ctc)
        if not validation_result['valid']:
            return {'success': False, 'error': validation_result['error']}
        
        # Use the auto-adjusted values from validation
        if 'auto_adjustments' in validation_result:
            updated_package.update(validation_result['auto_adjustments'])
        else:
            updated_package.update(changes)
        
        # Recalculate deductions (tax, UIF) based on updated package
        tax_calculations = calculate_employee_deductions(updated_package)
        updated_package.update(tax_calculations)
        
        # Add tax/UIF recalculation to audit trail
        for calc_field in ['paye_tax', 'uif_contribution']:
            current_calc_value = current_package.get(calc_field, 0)
            new_calc_value = tax_calculations[calc_field]
            if abs(float(current_calc_value) - float(new_calc_value)) > 0.01:
                audit_entries.append({
                    'timestamp': datetime.now().isoformat(),
                    'admin_user': 'SYSTEM',
                    'field_name': calc_field,
                    'old_value': current_calc_value,
                    'new_value': new_calc_value,
                    'action': 'auto_calculation'
                })
        
        # Add deduction calculations to audit trail
        for calc_field in ['paye_tax', 'uif_contribution', 'total_deductions']:
            if calc_field in tax_calculations:
                current_calc_value = current_package.get(calc_field, 0)
                new_calc_value = tax_calculations[calc_field]
                if abs(float(current_calc_value) - float(new_calc_value)) > 0.01:  # Only log if significantly different
                    audit_entries.append({
                        'timestamp': datetime.now().isoformat(),
                        'admin_user': 'SYSTEM',
                        'field_name': calc_field,
                        'old_value': current_calc_value,
                        'new_value': new_calc_value,
                        'action': 'auto_calculation'
                    })
        
        # Add all audit entries
        all_audits[employee_id].extend(audit_entries)
        
        # Save audit trail
        with open(audit_file, 'w') as f:
            json.dump(all_audits, f, indent=2)
        
        # Update the actual employee data in persistent storage
        try:
            # Get the latest SAP upload data
            if package_builder.sap_uploads:
                recent_uploads = package_builder.sap_uploads
                recent_uploads.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
                latest_upload = recent_uploads[0]
                
                if 'employee_data' in latest_upload:
                    # Find and update the employee data
                    for i, emp_data in enumerate(latest_upload['employee_data']):
                        if str(emp_data.get('EMPLOYEECODE', '')) == str(employee_id):
                            # Update all the changed fields
                            field_mapping = {
                                'basic_salary': 'TPE',
                                'car_allowance': 'CAR',
                                'medical_aid': 'MEDICAL',
                                'housing_allowance': 'HOUSING',
                                'transport_allowance': 'TRANSPORT',
                                'bonus': 'BONUSPROVISION',
                                'pension_fund': 'PENSIONCONTRIBUTIONFUND',
                                'paye_tax': 'PAYETAX',
                                'uif_contribution': 'UIF'
                            }
                            
                            for field_name, new_value in updated_package.items():
                                if field_name in field_mapping:
                                    latest_upload['employee_data'][i][field_mapping[field_name]] = new_value
                            
                            logger.info(f"Updated employee {employee_id} data in persistent storage")
                            break
                    
                    # Save the updated data back to persistent storage
                    package_builder.save_data()
                    logger.info(f"Saved updated employee data to persistent storage")
                    
        except Exception as e:
            logger.warning(f"Could not update persistent storage: {str(e)}")
        
        logger.info(f"Package changes saved for {employee_id} by {admin_user}: {changes}")
        
        return {
            'success': True, 
            'updated_data': {
                'basic_salary': updated_package.get('basic_salary'),
                'car_allowance': updated_package.get('car_allowance'),
                'bonus': updated_package.get('bonus'),
                'paye_tax': updated_package.get('paye_tax'),
                'uif_contribution': updated_package.get('uif_contribution'),
                'pension_fund': updated_package.get('pension_fund'),
                'total_deductions': updated_package.get('total_deductions')
            }
        }
        
    except Exception as e:
        logger.error(f"Error saving package changes: {str(e)}")
        return {'success': False, 'error': str(e)}

def get_employee_notifications(employee_id):
    """Get notifications for an employee"""
    try:
        notifications_file = 'randwater_notifications.json'
        if os.path.exists(notifications_file):
            with open(notifications_file, 'r') as f:
                all_notifications = json.load(f)
                return all_notifications.get(employee_id, [])
        return []
    except Exception as e:
        logger.error(f"Error loading notifications for {employee_id}: {str(e)}")
        return []

def create_employee_notification(employee_id, message, admin_user):
    """Create a notification for an employee"""
    try:
        notification = {
            'id': f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'admin_user': admin_user,
            'read': False,
            'type': 'package_update'
        }
        
        # Load existing notifications
        notifications_file = 'randwater_notifications.json'
        if os.path.exists(notifications_file):
            with open(notifications_file, 'r') as f:
                all_notifications = json.load(f)
        else:
            all_notifications = {}
        
        # Add new notification
        if employee_id not in all_notifications:
            all_notifications[employee_id] = []
        all_notifications[employee_id].append(notification)
        
        # Keep only last 20 notifications per employee
        all_notifications[employee_id] = all_notifications[employee_id][-20:]
        
        # Save notifications
        with open(notifications_file, 'w') as f:
            json.dump(all_notifications, f, indent=2)
            
        logger.info(f"Notification created for {employee_id}: {message}")
        
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")

def create_employee_access_records(df, current_user):
    """Create employee access records for O-Q band employees from SAP data"""
    try:
        logger.info("Creating employee access records...")
        
        # Load existing employee access data
        employee_access = []
        try:
            with open('employee_access.json', 'r') as f:
                employee_access = json.load(f)
            logger.info(f"Loaded {len(employee_access)} existing employee access records")
        except Exception as e:
            logger.info(f"No existing employee access file found: {e}")
        
        # Get existing employee IDs to avoid duplicates
        existing_ids = {emp['employee_id'] for emp in employee_access}
        
        created_count = 0
        current_date = datetime.now().strftime('%Y-%m-%d')
        access_expires = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Process each row in the DataFrame
        for index, row in df.iterrows():
            employee_id = str(row.get('EMPLOYEECODE', '')).strip()
            band = str(row.get('BAND', '')).upper().strip()
            
            # Only create access for O-Q band employees
            if band in ['O', 'P', 'Q'] and employee_id and employee_id not in existing_ids:
                first_name = str(row.get('FIRSTNAME', '')).strip()
                surname = str(row.get('SURNAME', '')).strip()
                
                # Generate username (lowercase employee ID)
                username = employee_id.lower()
                
                # Generate temporary password
                import random
                import string
                temp_password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
                
                # Create employee access record
                employee_record = {
                    'employee_id': employee_id,
                    'username': username,
                    'password': temp_password,
                    'first_name': first_name,
                    'surname': surname,
                    'band': band,
                    'status': 'ACTIVE',
                    'access_granted': current_date,
                    'access_expires': access_expires,
                    'created_date': datetime.now().isoformat(),
                    'created_by': current_user
                }
                
                employee_access.append(employee_record)
                created_count += 1
                
                logger.info(f"Created access record for {employee_id} ({first_name} {surname}) - Band {band}")
        
        # Save updated employee access data
        if created_count > 0:
            with open('employee_access.json', 'w') as f:
                json.dump(employee_access, f, indent=2)
            
            logger.info(f"✓ Created {created_count} new employee access records")
            logger.info(f"✓ Total employee access records: {len(employee_access)}")
        else:
            logger.info("No new employee access records needed")
            
    except Exception as e:
        logger.error(f"Error creating employee access records: {str(e)}")

def get_active_randwater_employees():
    """Get active Rand Water employees from uploaded SAP data and employee access"""
    try:
        logger.info("Getting active Rand Water employees...")
        
        # Load submitted packages to check submission status
        submitted_packages_map = {}
        try:
            if os.path.exists('submitted_packages.json'):
                with open('submitted_packages.json', 'r') as f:
                    submitted_packages = json.load(f)
                    for pkg in submitted_packages:
                        if pkg.get('status') == 'submitted':
                            submitted_packages_map[pkg['employee_id']] = True
                    logger.info(f"Found {len(submitted_packages_map)} submitted packages")
        except Exception as e:
            logger.warning(f"Could not load submitted packages: {e}")
        
        # First, try to get employees from employee_access.json
        employee_access_data = []
        try:
            with open('employee_access.json', 'r') as f:
                employee_access_data = json.load(f)
            logger.info(f"Found {len(employee_access_data)} employee access records")
        except Exception as e:
            logger.info(f"No employee access data found: {e}")
        
        if employee_access_data:
            # Get SAP data to merge with employee access data
            sap_data = {}
            try:
                sap_uploads = load_sap_uploads()
                print(f"\n=== SAP DATA DEBUG START ===")
                print(f"SAP uploads found: {len(sap_uploads) if sap_uploads else 0}")
                if sap_uploads:
                    latest_upload = max(sap_uploads, key=lambda x: x['upload_date'])
                    print(f"Latest upload: {latest_upload.get('filename', 'Unknown')}")
                    print(f"Employee data count: {len(latest_upload.get('employee_data', []))}")
                    
                    # Debug the first employee's data structure
                    if latest_upload.get('employee_data'):
                        first_emp = latest_upload['employee_data'][0]
                        print(f"First employee data keys: {list(first_emp.keys())}")
                        print(f"First employee EMPLOYEECODE: {first_emp.get('EMPLOYEECODE')}")
                        print(f"First employee TPE: {first_emp.get('TPE')}")
                        print(f"First employee HOUSING: {first_emp.get('HOUSING')}")
                        print(f"First employee PENSIONEECONTRIBUTION: {first_emp.get('PENSIONEECONTRIBUTION')}")
                        print(f"First employee MEDICALEECONTRIBUTION: {first_emp.get('MEDICALEECONTRIBUTION')}")
                    
                    sap_data = {emp['EMPLOYEECODE']: emp for emp in latest_upload.get('employee_data', [])}
                    print(f"SAP data loaded for employees: {list(sap_data.keys())}")
                    logger.info(f"Loaded SAP data for {len(sap_data)} employees")
                else:
                    print("No SAP uploads found!")
                print(f"=== SAP DATA DEBUG END ===\n")
            except Exception as e:
                print(f"SAP data loading error: {e}")
                logger.warning(f"Could not load SAP data: {e}")
            
            # Convert employee access data to employee format, merging with SAP data
            employees = []
            for emp_access in employee_access_data:
                employee_id = emp_access['employee_id']
                sap_emp = sap_data.get(employee_id, {})
                
                print(f"Processing employee {employee_id}:")
                print(f"  SAP data found: {bool(sap_emp)}")
                print(f"  TPE: {sap_emp.get('TPE', 'Not found')}")
                print(f"  CAR: {sap_emp.get('CAR', 'Not found')}")
                print(f"  TCTC: {sap_emp.get('TCTC', 'Not found')}")
                
                # Check if package has been submitted and get submitted values
                is_submitted = submitted_packages_map.get(employee_id, False)
                submitted_pkg = None
                if is_submitted:
                    for pkg in submitted_packages:
                        if pkg.get('employee_id') == employee_id and pkg.get('status') == 'submitted':
                            submitted_pkg = pkg
                            break
                
                # Build employee data - use submitted values if available
                submitted_comps = submitted_pkg.get('package_components', {}) if submitted_pkg else {}
                
                # Include ALL employees, not just ACTIVE ones
                employee = {
                    'employee_id': employee_id,
                    'first_name': emp_access.get('first_name', sap_emp.get('FIRSTNAME', '')),
                    'surname': emp_access.get('surname', sap_emp.get('SURNAME', '')),
                    'grade_band': emp_access.get('band', sap_emp.get('BAND', 'O-Q')),
                    'department': sap_emp.get('DEPARTMENT', 'General'),
                    'job_title': sap_emp.get('JOBLONG', 'Employee'),
                    'basic_salary': float(submitted_comps.get('tpe', sap_emp.get('TPE', 0))),
                    'car_allowance': float(submitted_comps.get('car_allowance', sap_emp.get('CAR', 0))),
                    'housing_allowance': float(submitted_comps.get('housing_allowance', sap_emp.get('HOUSING', 0))),
                    'cellphone_allowance': float(submitted_comps.get('cellphone_allowance', sap_emp.get('CELLPHONEALLOWANCE', 0))),
                    'data_service_allowance': float(submitted_comps.get('data_service_allowance', sap_emp.get('DATASERVICEALLOWANCE', 0))),
                    'pension_fund': float(submitted_comps.get('pension_fund', sap_emp.get('PENSIONEECONTRIBUTION', 0))),
                    'pension_er_contribution': float(submitted_comps.get('pension_er', sap_emp.get('PENSIONERCONTRIBUTION', 0))),
                    'medical_aid': float(sap_emp.get('MEDICALEECONTRIBUTION', 0)),
                    'medical_er_contribution': float(sap_emp.get('MEDICALERCONTRIBUTION', 0)),
                    'medical_ee_contribution': float(sap_emp.get('MEDICALEECONTRIBUTION', 0)),
                    'group_life_ee_contribution': float(submitted_comps.get('group_life_ee', sap_emp.get('GROUPLIFEEECONTRIBUTION', 0))),
                    'group_life_er_contribution': float(submitted_comps.get('group_life_er', sap_emp.get('GROUPLIFEERCONTRIBUTION', 0))),
                    'bonus': float(submitted_comps.get('bonus', sap_emp.get('BONUSPROVISION', 0))),
                    'critical_skills': float(sap_emp.get('CRITICALSKILLS', 0)),
                    'ctc': float(sap_emp.get('TCTC', 0)),
                    'pension_ee': float(submitted_comps.get('pension_ee', sap_emp.get('PENSIONEECONTRIBUTION', 0))),
                    'pension_er': float(submitted_comps.get('pension_er', sap_emp.get('PENSIONERCONTRIBUTION', 0))),
                    'group_life_ee': float(submitted_comps.get('group_life_ee', sap_emp.get('GROUPLIFEEECONTRIBUTION', 0))),
                    'group_life_er': float(submitted_comps.get('group_life_er', sap_emp.get('GROUPLIFEERCONTRIBUTION', 0))),
                    'cash_component': float(submitted_comps.get('cash_component', 0)),
                    'access_granted': emp_access.get('access_granted', ''),
                    'access_expires': emp_access.get('access_expires', ''),
                    'days_remaining': 30,
                    'package_submitted': is_submitted,
                    'is_expired': emp_access.get('status') != 'ACTIVE',
                    'username': emp_access.get('username', ''),
                    'access_status': emp_access.get('status', 'ACTIVE'),
                    'employee_subgroup': emp_access.get('employee_subgroup', 'other'),
                    'band_range': emp_access.get('band_range', 'o_to_q'),
                    'pension_option': emp_access.get('pension_option', 'B'),
                    'group_life_option': emp_access.get('group_life_option', 'standard'),
                    'bonus_type': emp_access.get('bonus_type', 'monthly'),
                    'medical_provider': sap_emp.get('MEDICAL', 'N/A'),
                    'medical_option': sap_emp.get('MEDICALOPTION', 'N/A'),
                    'medical_er_contribution_full': float(sap_emp.get('MEDICALERCONTRIBUTION', 0))
                }
                employees.append(employee)
            
            logger.info(f"Returning {len(employees)} employees from employee access data with SAP data (including revoked)")
            return employees
        
        # Fallback: try to get employees from completed packages
        completed_packages = get_all_randwater_completed_packages()
        logger.info(f"Found {len(completed_packages)} completed packages")
        
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
                        'access_granted': package.get('submission_date', datetime.now().strftime('%Y-%m-%d')),
                        'access_expires': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                        'days_remaining': 30,  # Actual calculation
                        'package_submitted': package.get('status') == 'COMPLETED',
                        'is_expired': False
                    }
                    employees.append(employee)
            
            return employees
        
        # If no completed packages, check if we have uploaded SAP data
        logger.info("No completed packages found, checking for uploaded SAP data...")
        filepath = None
        if session.get('last_upload'):
            filepath = session['last_upload']['filepath']
            logger.info(f"Found session upload: {filepath}")
        else:
            logger.info("No session upload found, trying persistent storage...")
            # Try to restore from persistent storage
            try:
                recent_uploads = package_builder.sap_uploads
                logger.info(f"Found {len(recent_uploads)} uploads in persistent storage")
                if recent_uploads:
                    # Sort by upload date and get the most recent
                    recent_uploads.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
                    latest_upload = recent_uploads[0]
                    filepath = os.path.join('uploads', latest_upload['filename'])
                    
                    # Restore session data for this upload
                    session['last_upload'] = {
                        'filename': latest_upload['filename'],
                        'filepath': filepath,
                        'upload_time': latest_upload['upload_date'],
                        'upload_id': latest_upload['id']
                    }
                    logger.info(f"Restored session from persistent storage: {latest_upload['filename']}")
            except Exception as e:
                logger.warning(f"Could not restore from persistent storage: {str(e)}")
        
        if filepath:
            logger.info(f"Attempting to read SAP file: {filepath}")
            try:
                import pandas as pd
                
                if os.path.exists(filepath):
                    logger.info(f"File exists, reading Excel file...")
                    # Read the Excel file
                    df = pd.read_excel(filepath)
                    logger.info(f"Successfully read {len(df)} rows from Excel file")
                    
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
                        access_expires = str(row.get('ACCESSEXPIRES', (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))) if 'ACCESSEXPIRES' in df.columns and pd.notna(row.get('ACCESSEXPIRES')) else (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                        
                        # Calculate actual days remaining
                        try:
                            from datetime import date
                            expiry_date = datetime.strptime(access_expires, '%Y-%m-%d').date()
                            today = date.today()
                            days_remaining = (expiry_date - today).days
                            is_expired = days_remaining < 0
                        except:
                            days_remaining = 30
                            is_expired = False
                        
                        # Only include employees in O, P, or Q bands
                        if grade_band.upper() in ['O', 'P', 'Q']:
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
                        else:
                            logger.info(f"Excluding employee {employee_id} ({first_name} {surname}) - Band {grade_band} not in O-Q range")
                    
                    logger.info(f"Converted {len(employees)} employees from SAP data (filtered by O-Q bands)")
                    return employees
                else:
                    logger.warning(f"SAP file does not exist: {filepath}")
                    # Try to use data from persistent storage instead
                    try:
                        recent_uploads = package_builder.sap_uploads
                        if recent_uploads:
                            # Sort by upload date and get the most recent
                            recent_uploads.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
                            latest_upload = recent_uploads[0]
                            
                            if 'employee_data' in latest_upload:
                                logger.info(f"Using employee data from persistent storage: {len(latest_upload['employee_data'])} employees")
                                
                                # Convert stored employee data to the expected format
                                employees = []
                                for emp_data in latest_upload['employee_data']:
                                    employee_id = str(emp_data.get('EMPLOYEECODE', f"RW{len(employees)+1:03d}"))
                                    first_name = str(emp_data.get('FIRSTNAME', ''))
                                    surname = str(emp_data.get('SURNAME', ''))
                                    grade_band = str(emp_data.get('BAND', 'O-Q'))
                                    department = str(emp_data.get('DEPARTMENT', 'General'))
                                    job_title = str(emp_data.get('JOBLONG', 'Employee'))
                                    basic_salary = float(emp_data.get('TPE', 0))
                                    ctc = float(emp_data.get('CTC', 0))
                                    
                                    # Use current date for access dates
                                    access_granted = datetime.now().strftime('%Y-%m-%d')
                                    access_expires = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                                    
                                    # Only include employees in O, P, or Q bands
                                    if grade_band.upper() in ['O', 'P', 'Q']:
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
                                            'days_remaining': 30,
                                            'package_submitted': False,
                                            'is_expired': False
                                        }
                                        employees.append(employee)
                                    else:
                                        logger.info(f"Excluding employee {employee_id} ({first_name} {surname}) - Band {grade_band} not in O-Q range")
                                
                                logger.info(f"Successfully converted {len(employees)} employees from persistent storage (filtered by O-Q bands)")
                                return employees
                        
                    except Exception as e:
                        logger.error(f"Error using persistent storage data: {str(e)}")
                    
            except Exception as e:
                logger.error(f"Error reading uploaded SAP file: {str(e)}")
                return []
        
        # If no session data, try to use persistent storage data directly
        try:
            recent_uploads = package_builder.sap_uploads
            if recent_uploads:
                # Sort by upload date and get the most recent
                recent_uploads.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
                latest_upload = recent_uploads[0]
                
                if 'employee_data' in latest_upload:
                    logger.info(f"Loading employees directly from persistent storage: {len(latest_upload['employee_data'])} employees")
                    
                    # Convert stored employee data to the expected format
                    employees = []
                    for emp_data in latest_upload['employee_data']:
                        employee_id = str(emp_data.get('EMPLOYEECODE', f"RW{len(employees)+1:03d}"))
                        first_name = str(emp_data.get('FIRSTNAME', ''))
                        surname = str(emp_data.get('SURNAME', ''))
                        grade_band = str(emp_data.get('BAND', 'O-Q'))
                        department = str(emp_data.get('DEPARTMENT', 'General'))
                        job_title = str(emp_data.get('JOBLONG', 'Employee'))
                        basic_salary = float(emp_data.get('TPE', 0))
                        ctc = float(emp_data.get('CTC', 0))
                        
                        # Use current date for access dates
                        access_granted = datetime.now().strftime('%Y-%m-%d')
                        access_expires = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                        
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
                            'days_remaining': 30,
                            'package_submitted': False,
                            'is_expired': False
                        }
                        employees.append(employee)
                    
                    logger.info(f"Successfully loaded {len(employees)} employees from persistent storage")
                    return employees
                    
        except Exception as e:
            logger.error(f"Error loading from persistent storage: {str(e)}")
        
        return []
        
    except Exception as e:
        logger.error(f"Error getting active Rand Water employees: {str(e)}")
        return []

# ============================================================================
# HELPER FUNCTIONS FOR USER MANAGEMENT
# ============================================================================

def save_system_log(log_entry):
    """Save system log entry for admin viewing"""
    try:
        logs_file = 'system_logs.json'
        logs = []
        
        # Load existing logs
        if os.path.exists(logs_file):
            try:
                with open(logs_file, 'r') as f:
                    logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
        
        # Add new log entry with ID
        log_entry['id'] = len(logs) + 1
        logs.append(log_entry)
        
        # Keep only last 100 logs
        logs = logs[-100:]
        
        # Save logs
        with open(logs_file, 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving system log: {str(e)}")

def load_system_logs():
    """Load system logs for admin viewing"""
    try:
        logs_file = 'system_logs.json'
        if os.path.exists(logs_file):
            with open(logs_file, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading system logs: {str(e)}")
        return []

def load_sap_uploads():
    """Load SAP uploads from JSON file"""
    try:
        with open('sap_uploads.json', 'r') as f:
            uploads = json.load(f)
            return uploads
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        logger.warning("Corrupted SAP uploads file")
        return []

def load_system_users():
    """Load system users from JSON file"""
    try:
        with open('system_users.json', 'r') as f:
            users = json.load(f)
            return users
    except FileNotFoundError:
        # Create default users if file doesn't exist
        default_users = [
            {
                'id': 1,
                'username': 'superadmin',
                'password': 'SuperSecret2024!',
                'profile': 'superadmin',
                'full_name': 'System Super Administrator',
                'email': 'superadmin@randwater.co.za',
                'status': 'active',
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_login': None
            },
            {
                'id': 2,
                'username': 'randwateradmin',
                'password': 'RandWater2024!',
                'profile': 'admin',
                'full_name': 'Rand Water Administrator',
                'email': 'admin@randwater.co.za',
                'status': 'active',
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_login': None
            }
        ]
        save_system_users(default_users)
        return default_users
    except Exception as e:
        logger.error(f"Error loading system users: {str(e)}")
        return []

def save_system_users(users):
    """Save system users to JSON file"""
    try:
        with open('system_users.json', 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving system users: {str(e)}")
        return False


# ============================================================================
# PASSWORD RESET SUPPORT
# ============================================================================

TOKENS_FILE = 'password_reset_tokens.json'


def _load_tokens() -> List[dict]:
    try:
        with open(TOKENS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.error(f"Error loading tokens: {e}")
        return []


def _save_tokens(tokens: List[dict]) -> None:
    try:
        with open(TOKENS_FILE, 'w') as f:
            json.dump(tokens, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving tokens: {e}")


def _prune_tokens(tokens: List[dict]) -> List[dict]:
    now = datetime.utcnow()
    valid: List[dict] = []
    for t in tokens:
        try:
            if datetime.fromisoformat(t.get('expires_at')) > now:
                valid.append(t)
        except Exception:
            continue
    return valid


def send_email(subject: str, to_address: str, html_body: str, text_body: Optional[str] = None) -> bool:
    cfg = RANDWATER_CONFIG.get('smtp', {})
    print(f"=== EMAIL DEBUG START ===")
    print(f"SMTP Config: {cfg}")
    print(f"Subject: {subject}")
    print(f"To: {to_address}")
    print(f"From: {cfg.get('from_address')}")
    
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = cfg.get('from_address')
        msg['To'] = to_address
        msg.set_content(text_body or 'Use an HTML capable email client to view this message.')
        msg.add_alternative(html_body, subtype='html')
        print(f"Email message created successfully")

        print(f"Connecting to SMTP server: {cfg.get('host')}:{cfg.get('port')}")
        with smtplib.SMTP(cfg.get('host'), cfg.get('port')) as server:
            print(f"Connected to SMTP server")
            if cfg.get('use_tls', True):
                print(f"Starting TLS...")
                server.starttls()
                print(f"TLS started successfully")
            print(f"Logging in with username: {cfg.get('username')}")
            server.login(cfg.get('username'), cfg.get('password'))
            print(f"Login successful")
            print(f"Sending message...")
            server.send_message(msg)
            print(f"Message sent successfully")
        print(f"=== EMAIL DEBUG SUCCESS ===")
        return True
    except Exception as e:
        print(f"=== EMAIL DEBUG ERROR ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        logger.error(f"SMTP send failed: {e}")
        return False


def _find_user_by_username_or_email(identifier: str) -> Optional[dict]:
    users = load_system_users()
    ident_lower = (identifier or '').strip().lower()
    for u in users:
        if u.get('username', '').lower() == ident_lower or u.get('email', '').lower() == ident_lower:
            return u
    return None


def _update_user_password(user_id: int, new_password_plain: str) -> bool:
    users = load_system_users()
    updated = False
    for u in users:
        if u.get('id') == user_id:
            # store hashed
            u['password'] = generate_password_hash(new_password_plain)
            updated = True
            break
    if updated:
        return save_system_users(users)
    return False

# ============================================================================
# EMPLOYEE AND SUPER ADMIN ROUTES
# ============================================================================

# Simple employee and super admin routes added

# ============================================================================
# EMPLOYEE ROUTES
# ============================================================================

@app.route('/debug')
def debug_info():
    """Debug endpoint to check app status"""
    system_users = load_system_users()
    return {
        'app_running': True,
        'users_count': len(system_users),
        'users': [{'username': u['username'], 'profile': u['profile']} for u in system_users],
        'test_password': 'Anna2537',
        'test_username': 'RandWaterAdmin'
    }

@app.route('/login', methods=['GET', 'POST'])
def unified_login():
    """Unified login for all user types - routes to appropriate dashboard"""
    error = None
    
    if request.method == 'POST':
        raw_username = request.form.get('username') or ''
        username = raw_username.strip().lower()
        password = (request.form.get('password') or '').strip()
        
        if not username or not password:
            error = "Please enter both username and password"
            return render_template('unified_login.html', error=error, config=RANDWATER_CONFIG)
        
        # Load system users and check credentials
        system_users = load_system_users()
        
        # DEBUG: Print comprehensive login debugging info
        print(f"\n=== LOGIN DEBUG START ===")
        print(f"Raw username input: '{raw_username}'")
        print(f"Processed username: '{username}'")
        print(f"Password length: {len(password)}")
        print(f"Number of system users: {len(system_users)}")
        
        for i, user in enumerate(system_users):
            print(f"User {i+1}: username='{user.get('username')}', profile='{user.get('profile')}', status='{user.get('status')}'")
            stored_pw = user.get('password', '')
            print(f"  Password hash: {stored_pw[:50]}..." if len(stored_pw) > 50 else f"  Password: {stored_pw}")
        
        try:
            logger.info(f"Login attempt username='{username}'")
            logger.info(f"Available system usernames={[str(u.get('username','')).strip().lower() for u in system_users]}")
        except Exception as e:
            print(f"Logger error: {e}")
        
        user_found = False
        username_matched = False
        
        for user in system_users:
            stored_pw = user.get('password', '')
            is_hashed = isinstance(stored_pw, str) and (':' in stored_pw)
            valid = (stored_pw == password)
            db_username = str(user.get('username', '')).strip().lower()
            
            print(f"\nChecking user: '{db_username}' vs '{username}'")
            print(f"  Password match (plain): {valid}")
            print(f"  Is hashed: {is_hashed}")
            
            if db_username == username:
                username_matched = True
                print(f"  *** USERNAME MATCHED! ***")
                if not valid and is_hashed:
                    try:
                        valid = check_password_hash(stored_pw, password)
                        print(f"  Password hash check result: {valid}")
                    except Exception as e:
                        print(f"  Hash check error: {e}")
                        valid = False
                else:
                    print(f"  Using plain text comparison: {valid}")
            
            if db_username == username and valid:
                if user['status'] != 'active':
                    error = "Account is inactive. Please contact administrator."
                    user_found = True
                    break
                
                # Check password expiry
                is_expired, expiry_message = check_password_expiry(user['id'])
                if is_expired:
                    error = f"Password expired. {expiry_message}. Please reset your password."
                    user_found = True
                    break
                
                # Update last login
                user['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                save_system_users(system_users)
                
                # Set session based on profile
                if user['profile'] == 'superadmin':
                    session['isSuperAdmin'] = True
                    session['super_admin'] = True
                    session['username'] = username
                    logger.info(f"Super Admin {username} logged in successfully")
                    return redirect(url_for('super_admin_dashboard'))
                
                elif user['profile'] == 'admin':
                    session['admin'] = True
                    session['isRandWaterAdmin'] = True
                    session['username'] = username
                    logger.info(f"Randwater Admin {username} logged in successfully")
                    return redirect(url_for('randwater_admin_panel'))
                
                else:
                    error = "Invalid user profile"
                    user_found = True
                    break
        
        # If username matched but password invalid, show specific error
        if not user_found and username_matched:
            error = "Invalid password"
            user_found = True

        # If no system user found, check employees
        if not user_found:
            print(f"\n=== CHECKING EMPLOYEES ===")
            try:
                # First check if employee exists in employee_access.json (regardless of status)
                employee_access_data = []
                try:
                    with open('employee_access.json', 'r') as f:
                        employee_access_data = json.load(f)
                except:
                    pass
                
                # Check if employee exists in access data
                employee_in_system = None
                for emp_access in employee_access_data:
                    if emp_access['employee_id'].lower() == username:
                        employee_in_system = emp_access
                        break
                
                if employee_in_system:
                    print(f"*** EMPLOYEE FOUND IN SYSTEM: {employee_in_system['employee_id']} ***")
                    print(f"Status: {employee_in_system.get('status', 'UNKNOWN')}")
                    
                    # Check if access is revoked or expired
                    if employee_in_system.get('status') == 'REVOKED':
                        error = "Access Expired/Revoked"
                        employee_found = True
                    elif employee_in_system.get('status') == 'EXPIRED':
                        error = "Access Expired/Revoked"
                        employee_found = True
                    else:
                        # Check if access has expired by date
                        access_expires = employee_in_system.get('access_expires')
                        if access_expires:
                            try:
                                expire_date = datetime.strptime(access_expires, '%Y-%m-%d')
                                if datetime.now() > expire_date:
                                    error = "Access Expired/Revoked"
                                    employee_found = True
                                else:
                                    # Access is still valid, check password
                                    if password == employee_in_system.get('password', ''):
                                        # Get employee from active list for session data
                                        active_employees = get_active_randwater_employees()
                                        for employee in active_employees:
                                            if employee['employee_id'].lower() == username:
                                                session['employee_id'] = employee['employee_id']
                                                session['username'] = username
                                                session['employee_name'] = f"{employee.get('first_name', '')} {employee.get('surname', '')}".strip()
                                                logger.info(f"Employee {employee['employee_id']} logged in successfully")
                                                return redirect(url_for('employee_dashboard'))
                                        error = "Employee access error"
                                        employee_found = True
                                    else:
                                        error = "Invalid password"
                                        employee_found = True
                            except:
                                error = "Access Expired/Revoked"
                                employee_found = True
                        else:
                            error = "Access Expired/Revoked"
                            employee_found = True
                else:
                    print(f"*** EMPLOYEE NOT FOUND IN SYSTEM ***")
                    # Check active employees for additional context
                    active_employees = get_active_randwater_employees()
                    print(f"Number of active employees: {len(active_employees)}")
                    employee_found = False
                    for employee in active_employees:
                        print(f"Checking active employee: '{employee['employee_id'].lower()}' vs '{username}'")
                        if employee['employee_id'].lower() == username:
                            print(f"  *** EMPLOYEE USERNAME MATCHED! ***")
                            # Check if employee access has expired
                            if employee.get('is_expired', False):
                                error = "Your access has expired. Please contact administrator."
                                employee_found = True
                                break
                            
                            # Validate password (using temporary password for now)
                            if password == 'TempPass123':
                                session['employee_id'] = employee['employee_id']
                                session['username'] = username
                                session['employee_name'] = f"{employee.get('first_name', '')} {employee.get('surname', '')}".strip()
                                logger.info(f"Employee {employee['employee_id']} logged in successfully")
                                return redirect(url_for('employee_dashboard'))
                            else:
                                error = "Invalid password"
                                employee_found = True
                                break
                
                if not employee_found and not employee_in_system:
                    print(f"*** NO EMPLOYEE MATCH FOUND ***")
                    error = "Invalid username or user not found"
                    
            except Exception as e:
                print(f"*** EMPLOYEE CHECK ERROR: {str(e)} ***")
                logger.error(f"Error during login: {str(e)}")
                error = "Login system error. Please contact administrator."
        
        print(f"\n=== FINAL RESULT ===")
        print(f"User found: {user_found}")
        print(f"Username matched: {username_matched}")
        print(f"Final error: {error}")
        print(f"=== LOGIN DEBUG END ===\n")

    return render_template('unified_login.html', error=error, config=RANDWATER_CONFIG)


@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    """Request a password reset by username or email."""
    message = None
    error = None
    if request.method == 'POST':
        identifier = request.form.get('identifier', '')
        user = _find_user_by_username_or_email(identifier)
        if not user:
            error = 'User not found'
        else:
            tokens = _load_tokens()
            tokens = _prune_tokens(tokens)
            token = os.urandom(24).hex()
            expires = datetime.utcnow() + timedelta(hours=1)
            tokens.append({
                'token': token,
                'user_id': user['id'],
                'expires_at': expires.isoformat()
            })
            _save_tokens(tokens)

            reset_link = f"{RANDWATER_CONFIG['app_base_url']}/reset/{token}"
            html = f"""
                <p>Hello {user.get('full_name','')},</p>
                <p>You requested a password reset. Click the link below to set a new password:</p>
                <p><a href='{reset_link}'>{reset_link}</a></p>
                <p>This link will expire in 1 hour. If you did not request this, you can ignore this email.</p>
            """
            sent = send_email('Rand Water Calculator - Password Reset', user.get('email'), html)
            message = 'If the account exists, a reset email has been sent.' if sent else 'Failed to send reset email. Please try again later.'

    return render_template('forgot_password.html', message=message, error=error, config=RANDWATER_CONFIG)


@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token: str):
    """Handle password reset via token."""
    tokens = _prune_tokens(_load_tokens())
    matching = next((t for t in tokens if t.get('token') == token), None)
    if not matching:
        return render_template('reset_password.html', token=None, error='Invalid or expired reset link', config=RANDWATER_CONFIG)

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm = request.form.get('confirm')
        
        if not new_password or not confirm:
            return render_template('reset_password.html', token=token, error='Please fill in all fields', config=RANDWATER_CONFIG)
        
        if new_password != confirm:
            return render_template('reset_password.html', token=token, error='Passwords do not match', config=RANDWATER_CONFIG)
        
        # Validate password against policy
        is_valid, errors = validate_password_strength(new_password)
        if not is_valid:
            error_message = "Password does not meet requirements:<br>" + "<br>".join(f"• {error}" for error in errors)
            return render_template('reset_password.html', token=token, error=error_message, config=RANDWATER_CONFIG)
        
        # Check password history
        if not check_password_history(matching['user_id'], new_password):
            return render_template('reset_password.html', token=token, error='Password cannot be reused. Please choose a different password.', config=RANDWATER_CONFIG)

        # Get old password hash before updating
        system_users = load_system_users()
        user = next((u for u in system_users if u['id'] == matching['user_id']), None)
        old_password_hash = user.get('password', '') if user else ''

        ok = _update_user_password(matching['user_id'], new_password)
        if ok:
            # Update password history
            if old_password_hash:
                update_password_history(matching['user_id'], old_password_hash)
            
            tokens = [t for t in tokens if t.get('token') != token]
            _save_tokens(tokens)
            return redirect(url_for('unified_login'))
        return render_template('reset_password.html', token=token, error='Failed to update password', config=RANDWATER_CONFIG)

    return render_template('reset_password.html', token=token, error=None, config=RANDWATER_CONFIG)


@app.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    """Redirect to unified login"""
    return redirect(url_for('unified_login'))

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
    
    try:
        # Get employee data
        employee_id = session.get('employee_id')
        active_employees = get_active_randwater_employees()
        employee = None
        
        for emp in active_employees:
            if emp['employee_id'] == employee_id:
                employee = emp
                break
        
        if not employee:
            session.clear()
            return redirect(url_for('employee_login'))
        
        # Get notifications for this employee
        notifications = get_employee_notifications(employee_id)
        
        return render_template('employee_dashboard.html', 
                             employee=employee,
                             notifications=notifications,
                             config=RANDWATER_CONFIG)
    except Exception as e:
        logger.error(f"Error loading employee dashboard: {str(e)}")
        return redirect(url_for('employee_login'))

@app.route('/employee/package/<employee_id>')
def employee_package_details(employee_id):
    """Employee - View detailed package information (reuse fullpage edit interface)"""
    if not session.get('employee_id') or session.get('employee_id') != employee_id:
        return redirect(url_for('employee_login'))
    
    try:
        # Get employee data
        active_employees = get_active_randwater_employees()
        employee = None
        for emp in active_employees:
            if emp['employee_id'] == employee_id:
                employee = emp
                break
        
        if not employee:
            return redirect(url_for('employee_login'))
        
        # Check if package has been submitted - if so, redirect to dashboard with a message
        if employee.get('package_submitted', False):
            flash('This package has already been submitted and cannot be edited.', 'warning')
            return redirect(url_for('employee_dashboard'))
        
        # Get audit trail for this package (empty for employees)
        audit_trail = []
        
        # No notifications for employees on the edit page
        notifications = []
        
        # Use the same fullpage edit template as admin
        return render_template('package_edit_fullpage.html', 
                             config=RANDWATER_CONFIG,
                             employee=employee,
                             audit_trail=audit_trail,
                             notifications=notifications)
        
    except Exception as e:
        logger.error(f"Error loading employee package edit for {employee_id}: {str(e)}")
        return redirect(url_for('employee_dashboard'))

@app.route('/employee/package/<employee_id>/edit', methods=['POST'])
def employee_edit_package(employee_id):
    """Employee - Edit their own package details"""
    if not session.get('employee_id') or session.get('employee_id') != employee_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get the changes from the request
        changes = request.get_json()
        employee_name = session.get('employee_name', f'Employee {employee_id}')
        
        # Save the changes with audit trail (reuse existing function)
        result = save_package_changes(employee_id, changes, employee_name)
        
        if result['success']:
            # Create notification for admin about employee self-edit
            admin_notification = f"{employee_name} updated their own compensation package"
            logger.info(f"Employee {employee_id} self-edited package: {changes}")
            
            return jsonify({
                'success': True,
                'message': 'Package updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to save changes')
            })
            
    except Exception as e:
        logger.error(f"Error in employee package edit: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error while saving changes'
        }), 500

@app.route('/employee/payslip/<employee_id>')
def employee_payslip_view(employee_id):
    """Employee - View payslip (reuse existing payslip functionality)"""
    if not session.get('employee_id') or session.get('employee_id') != employee_id:
        return redirect(url_for('employee_login'))
    
    # Redirect to the existing payslip route but with employee context
    return redirect(f'/admin/randwater/employee-payslip/{employee_id}')

@app.route('/employee/download/<employee_id>')
def employee_download_summary(employee_id):
    """Employee - Download package summary"""
    if not session.get('employee_id') or session.get('employee_id') != employee_id:
        return redirect(url_for('employee_login'))
    
    # For now, show a coming soon message
    return f"""
    <html>
    <head><title>Download - Coming Soon</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h2>📄 Package Summary Download</h2>
        <p>This feature is coming soon!</p>
        <p>You'll be able to download a PDF summary of your compensation package.</p>
        <a href="/employee/dashboard" style="color: #0066CC;">← Back to Dashboard</a>
    </body>
    </html>
    """

@app.route('/employee/help')
def employee_help():
    """Employee - Help and support page"""
    if not session.get('employee_id'):
        return redirect(url_for('employee_login'))
    
    return f"""
    <html>
    <head><title>Help & Support</title></head>
    <body style="font-family: Arial; padding: 50px; max-width: 800px; margin: 0 auto;">
        <h2>🆘 Help & Support</h2>
        
        <h3>📞 Contact Information</h3>
        <p><strong>HR Support:</strong> hr@randwater.co.za</p>
        <p><strong>Phone:</strong> +27 11 123 4567</p>
        
        <h3>❓ Frequently Asked Questions</h3>
        <h4>Q: How long do I have access to this portal?</h4>
        <p>A: Your access is valid for 30 days from the date it was granted.</p>
        
        <h4>Q: Can I modify my package details?</h4>
        <p>A: No, only HR administrators can modify package details. Contact HR if changes are needed.</p>
        
        <h4>Q: What if I forgot my password?</h4>
        <p>A: Contact your HR administrator to reset your password.</p>
        
        <h4>Q: When will my new package take effect?</h4>
        <p>A: Package changes typically take effect from the next payroll cycle. Check with HR for specific dates.</p>
        
        <a href="/employee/dashboard" style="color: #0066CC; text-decoration: none;">← Back to Dashboard</a>
    </body>
    </html>
    """

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
    return redirect(url_for('super_admin_login'))

@app.route('/superadmin/dashboard')
def super_admin_dashboard():
    """Super Admin dashboard for system configuration"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    # Get real stats from the system
    try:
        active_employees = get_active_randwater_employees()
        total_employees = len(active_employees)
    except:
        total_employees = 0
    
    stats = {
        'total_superadmins': 1,  # Currently just one
        'total_randwater_admins': 1,  # Currently just one
        'total_employees': total_employees,
        'total_packages': total_employees,  # One package per employee
        'system_version': '2.0.0'
    }
    
    return render_template('super_admin_dashboard.html',
                          stats=stats,
                          config=RANDWATER_CONFIG)

@app.route('/superadmin/user-management')
def user_management():
    """Manage system users and their profiles"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    # Load existing users from JSON file
    users = load_system_users()
    
    return render_template('user_management.html', 
                          users=users, 
                          config=RANDWATER_CONFIG)

@app.route('/superadmin/user-management/create', methods=['POST'])
def create_user():
    """Create a new system user"""
    if not session.get('isSuperAdmin'):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        username = request.json.get('username')
        password = request.json.get('password')
        profile = request.json.get('profile')  # 'superadmin', 'admin', or 'employee'
        full_name = request.json.get('full_name')
        email = request.json.get('email')
        
        if not all([username, password, profile, full_name]):
            return jsonify({'success': False, 'error': 'All fields are required'})
        
        # Load existing users
        users = load_system_users()
        
        # Check if username already exists
        if any(user['username'].lower() == username.lower() for user in users):
            return jsonify({'success': False, 'error': 'Username already exists'})
        
        # Create new user
        new_user = {
            'id': len(users) + 1,
            'username': username,
            'password': password,  # In production, this should be hashed
            'profile': profile,
            'full_name': full_name,
            'email': email,
            'status': 'active',
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_login': None
        }
        
        users.append(new_user)
        save_system_users(users)
        
        logger.info(f"Super Admin created new user: {username} with profile: {profile}")
        return jsonify({'success': True, 'message': f'User {username} created successfully'})
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create user'})

@app.route('/superadmin/user-management/update/<int:user_id>', methods=['POST'])
def update_user(user_id):
    """Update a system user"""
    if not session.get('isSuperAdmin'):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        users = load_system_users()
        user = next((u for u in users if u['id'] == user_id), None)
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
        
        # Update user fields
        user['profile'] = request.json.get('profile', user['profile'])
        user['status'] = request.json.get('status', user['status'])
        user['full_name'] = request.json.get('full_name', user['full_name'])
        user['email'] = request.json.get('email', user['email'])
        
        # Update password if provided
        new_password = request.json.get('password')
        if new_password:
            user['password'] = new_password
        
        save_system_users(users)
        
        logger.info(f"Super Admin updated user: {user['username']}")
        return jsonify({'success': True, 'message': f'User {user["username"]} updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update user'})

@app.route('/superadmin/user-management/delete/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a system user"""
    if not session.get('isSuperAdmin'):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        users = load_system_users()
        user = next((u for u in users if u['id'] == user_id), None)
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
        
        # Don't allow deleting the current super admin
        if user['profile'] == 'superadmin' and user['username'].lower() == session.get('username', '').lower():
            return jsonify({'success': False, 'error': 'Cannot delete current super admin'})
        
        users = [u for u in users if u['id'] != user_id]
        save_system_users(users)
        
        logger.info(f"Super Admin deleted user: {user['username']}")
        return jsonify({'success': True, 'message': f'User {user["username"]} deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete user'})

# ============================================================================
# RAND WATER ADMIN ROUTES
# ============================================================================

@app.route('/admin/randwater/logout')
def randwater_admin_logout():
    """Randwater admin logout"""
    session.pop('admin', None)
    session.pop('isRandWaterAdmin', None)
    session.pop('user', None)
    # Keep the uploaded file data for persistence
    # session.pop('last_upload', None)  # Don't clear this - let it persist
    return redirect(url_for('randwater_admin_login'))

@app.route('/admin/randwater', methods=['GET', 'POST'])
def randwater_admin_login():
    """Redirect to unified login"""
    return redirect(url_for('unified_login'))

@app.route('/admin/randwater/dashboard')
def randwater_admin_panel():
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    settings = load_tax_settings()
    
    # Get active employees from uploaded SAP data
    active_employees = get_active_randwater_employees()
    total_employees = len(active_employees)
    
    # Count submitted packages
    submitted_count = len([e for e in active_employees if e.get('package_submitted', False)])
    pending_count = total_employees - submitted_count
    
    total_packages = total_employees
    completed_packages = submitted_count
    pending_packages = pending_count
    
    # Calculate completion rate safely
    completion_rate = 0.0
    if total_packages > 0:
        completion_rate = (completed_packages / total_packages) * 100
    
    logger.info(f"Dashboard: Found {total_employees} active employees, {submitted_count} submitted, {pending_count} pending")
    
    # Check for recent uploads from persistent storage if session is empty
    if not session.get('last_upload'):
        try:
            # Get the most recent upload from persistent storage
            if package_builder.sap_uploads:
                latest_upload = max(package_builder.sap_uploads, key=lambda x: x.get('upload_date', ''))
                if latest_upload:
                    # Check if file still exists
                    filepath = os.path.join('uploads', latest_upload['filename'])
                    if os.path.exists(filepath):
                        session['last_upload'] = {
                            'filename': latest_upload['filename'],
                            'filepath': filepath,
                            'upload_time': latest_upload['upload_date'],
                            'upload_id': latest_upload['id']
                        }
        except Exception as e:
            logger.warning(f"Could not retrieve recent uploads: {str(e)}")
    
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
    
    # Load current tax settings
    tax_settings = load_tax_settings()
    
    # Medical aid rates
    medical_aid_rates = {
        'rand_water': {
            'option_a': {'main': 364, 'adult': 364, 'child': 246},
            'option_b': {'main': 450, 'adult': 450, 'child': 320}
        },
        'bonitas': {
            'standard': {'main': 390, 'adult': 390, 'child': 280}
        }
    }
    
    # SARS tax brackets (2024)
    tax_brackets = [
        {'min': 0, 'max': 237100, 'rate': 18},
        {'min': 237101, 'max': 370500, 'rate': 26},
        {'min': 370501, 'max': 512800, 'rate': 31},
        {'min': 512801, 'max': 673000, 'rate': 36},
        {'min': 673001, 'max': 857900, 'rate': 39},
        {'min': 857901, 'max': 1817000, 'rate': 41},
        {'min': 1817001, 'max': 999999999, 'rate': 45}
    ]
    
    return render_template('calculation_tables.html', 
                          config=RANDWATER_CONFIG,
                          tax_settings=tax_settings,
                          medical_aid_rates=medical_aid_rates,
                          tax_brackets=tax_brackets)


@app.route('/security_settings')
def security_settings():
    """Super Admin - Security settings interface"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    return render_template('security_settings.html', config=RANDWATER_CONFIG)

@app.route('/system_backup')
def system_backup():
    """Super Admin - System backup interface"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    return render_template('system_backup.html', config=RANDWATER_CONFIG)

@app.route('/system_analytics')
def system_analytics():
    """Super Admin - System analytics interface"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    return render_template('system_analytics.html', config=RANDWATER_CONFIG)

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
        
        # Get financial year and period from form
        financial_year = request.form.get('financial_year', '2025')
        period = request.form.get('period', '')
        
        if not financial_year or not period:
            return jsonify({'error': 'Financial Year and Period are required'}), 400
        
        if file and file.filename.endswith('.xlsx'):
            # Save uploaded file with financial year and period in filename
            filename = f"randwater_sap_data_{financial_year}_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join('uploads', filename)
            os.makedirs('uploads', exist_ok=True)
            file.save(filepath)
            
            # Store upload info in session for immediate access
            session['last_upload'] = {
                'filename': filename,
                'filepath': filepath,
                'upload_time': datetime.now().isoformat(),
                'financial_year': financial_year,
                'period': period
            }
            
            # Also store in persistent storage
            try:
                # Read the Excel file to get employee data count
                import pandas as pd
                df = pd.read_excel(filepath)
                total_employees = len(df)
                
                logger.info(f"Successfully read Excel file with {total_employees} rows")
                
                # Count employees by band for statistics
                band_counts = {}
                opq_count = 0
                excluded_count = 0
                excluded_employees = []
                
                if 'BAND' in df.columns:
                    for index, row in df.iterrows():
                        band = str(row['BAND']).upper() if pd.notna(row['BAND']) else 'UNKNOWN'
                        band_counts[band] = band_counts.get(band, 0) + 1
                        
                        if band in ['O', 'P', 'Q']:
                            opq_count += 1
                        else:
                            excluded_count += 1
                            emp_id = str(row.get('EMPLOYEECODE', f'Unknown{index}'))
                            emp_name = f"{row.get('FIRSTNAME', '')} {row.get('SURNAME', '')}".strip()
                            excluded_employees.append(f"{emp_id} ({emp_name}) - Band {band}")
                
                # Get current user info
                current_user = session.get('username', 'Unknown User')
                upload_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                logger.info(f"")
                logger.info(f"=== UPLOAD STATISTICS ===")
                logger.info(f"Uploaded by: {current_user}")
                logger.info(f"Upload time: {upload_timestamp}")
                logger.info(f"File: {filename}")
                logger.info(f"Total employees uploaded: {total_employees}")
                logger.info(f"Employees in O-Q bands (Active): {opq_count}")
                logger.info(f"Employees excluded (Not O-Q): {excluded_count}")
                if excluded_employees:
                    logger.info(f"Excluded employees:")
                    for emp in excluded_employees:
                        logger.info(f"  - {emp}")
                logger.info(f"Band distribution: {band_counts}")
                logger.info(f"=========================")
                logger.info(f"")
                
                # Save to system logs file for admin viewing
                save_system_log({
                    'action': 'UPLOAD',
                    'user': current_user,
                    'timestamp': upload_timestamp,
                    'details': {
                        'filename': filename,
                        'total_employees': total_employees,
                        'active_employees': opq_count,
                        'excluded_employees': excluded_count,
                        'excluded_list': excluded_employees,
                        'band_distribution': band_counts
                    }
                })
                
                # Store in persistent storage
                try:
                    # Convert DataFrame to dict and handle Timestamp serialization
                    employee_data_dict = df.to_dict('records')
                    # Convert any Timestamp objects to strings
                    for emp in employee_data_dict:
                        for key, value in emp.items():
                            if pd.isna(value):
                                emp[key] = None
                            elif hasattr(value, 'isoformat'):  # Check if it's a datetime/Timestamp
                                emp[key] = value.isoformat()
                            elif isinstance(value, (int, float)) and pd.isna(value):
                                emp[key] = None
                    
                    upload_record = package_builder.upload_sap_data(
                        filename=filename,
                        upload_date=datetime.now().isoformat(),
                        employee_data=employee_data_dict,
                        financial_year=financial_year,
                        period=period
                    )
                    
                    # Update session with persistent ID
                    session['last_upload']['upload_id'] = upload_record['id']
                    logger.info("✓ Successfully stored upload in persistent storage")
                    
                    # Create employee access records for O-Q band employees
                    create_employee_access_records(df, current_user)
                    
                except Exception as storage_error:
                    logger.error(f"Error storing in persistent storage: {str(storage_error)}")
                    logger.info("Continuing with session storage only")
                
            except Exception as e:
                logger.error(f"Error processing Excel file: {str(e)}")
                logger.error(f"File path: {filepath}")
                logger.error(f"File exists: {os.path.exists(filepath)}")
                # Continue with session storage as fallback
                total_employees = 0
                opq_count = 0
                excluded_count = 0
            
            return jsonify({
                'success': True, 
                'filename': filename,
                'total_employees': total_employees,
                'active_employees': opq_count,
                'excluded_employees': excluded_count,
                'message': f'Successfully uploaded {total_employees} employees. {opq_count} in O-Q bands will be processed, {excluded_count} excluded.'
            })
        else:
            return jsonify({'error': 'Invalid file type. Please upload Excel (.xlsx) files only'}), 400
            
    except Exception as e:
        logger.error(f"Error uploading SAP data: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/admin/randwater/list-uploads')
def list_uploads():
    """Rand Water Admin - List all available SAP uploads"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        uploads = []
        for upload in package_builder.sap_uploads:
            filepath = os.path.join('uploads', upload['filename'])
            if os.path.exists(filepath):
                uploads.append({
                    'id': upload['id'],
                    'filename': upload['filename'],
                    'upload_date': upload['upload_date'],
                    'employee_count': upload['employee_count'],
                    'status': upload['status'],
                    'file_exists': True
                })
            else:
                uploads.append({
                    'id': upload['id'],
                    'filename': upload['filename'],
                    'upload_date': upload['upload_date'],
                    'employee_count': upload['employee_count'],
                    'status': upload['status'],
                    'file_exists': False
                })
        
        return jsonify({'uploads': uploads})
        
    except Exception as e:
        logger.error(f"Error listing uploads: {str(e)}")
        return jsonify({'error': 'Failed to list uploads'}), 500

@app.route('/admin/randwater/restore-upload/<int:upload_id>', methods=['POST'])
def restore_upload(upload_id):
    """Rand Water Admin - Restore a specific upload from persistent storage"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Find the upload in persistent storage
        upload = None
        for u in package_builder.sap_uploads:
            if u['id'] == upload_id:
                upload = u
                break
        
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404
        
        # Check if file still exists
        filepath = os.path.join('uploads', upload['filename'])
        if not os.path.exists(filepath):
            return jsonify({'error': 'File no longer exists on disk'}), 404
        
        # Restore to session
        session['last_upload'] = {
            'filename': upload['filename'],
            'filepath': filepath,
            'upload_time': upload['upload_date'],
            'upload_id': upload['id']
        }
        
        return jsonify({'success': True, 'message': f'Restored upload: {upload["filename"]}'})
        
    except Exception as e:
        logger.error(f"Error restoring upload: {str(e)}")
        return jsonify({'error': 'Failed to restore upload'}), 500

@app.route('/admin/randwater/archive-data', methods=['POST'])
def archive_current_data():
    """Rand Water Admin - Archive current financial year/period data"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        current_user = session.get('username', 'Unknown User')
        archive_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"")
        logger.info(f"=== DATA ARCHIVING OPERATION ===")
        logger.info(f"Archived by: {current_user}")
        logger.info(f"Archive time: {archive_timestamp}")
        
        archived_count = 0
        # Mark all current uploads as archived (set status to archived)
        if hasattr(package_builder, 'sap_uploads') and package_builder.sap_uploads:
            for upload in package_builder.sap_uploads:
                if not upload.get('status', '').startswith('ARCHIVED'):
                    upload['status'] = f"ARCHIVED_{archive_timestamp}"
                    archived_count += 1
                    
                    # Fix Timestamp serialization in employee_data
                    if 'employee_data' in upload and upload['employee_data']:
                        for emp in upload['employee_data']:
                            for key, value in emp.items():
                                if pd.notna(value) and hasattr(value, 'isoformat'):
                                    emp[key] = value.isoformat()
                                elif pd.isna(value):
                                    emp[key] = None
            
            package_builder.save_data()
            logger.info(f"✓ Archived {archived_count} SAP upload(s)")
        else:
            logger.info("- No uploads to archive")
        
        logger.info(f"=== DATA ARCHIVED SUCCESSFULLY ===")
        logger.info(f"")
        
        # Save to system logs
        save_system_log({
            'action': 'ARCHIVE_DATA',
            'user': current_user,
            'timestamp': archive_timestamp,
            'details': {
                'uploads_archived': archived_count
            }
        })
        
        return jsonify({
            'success': True, 
            'message': f'Successfully archived {archived_count} upload(s). Current data is now ready for a new upload.'
        })
        
    except Exception as e:
        logger.error(f"Error archiving data: {str(e)}")
        return jsonify({'error': f'Failed to archive data: {str(e)}'}), 500

@app.route('/admin/randwater/clear-uploaded-data', methods=['POST'])
def clear_uploaded_data():
    """Rand Water Admin - Clear current uploaded SAP data (preserves archived)"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        current_user = session.get('username', 'Unknown User')
        clear_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"")
        logger.info(f"=== DATA CLEARING OPERATION ===")
        logger.info(f"Cleared by: {current_user}")
        logger.info(f"Clear time: {clear_timestamp}")
        
        # Clear session data
        session.pop('last_upload', None)
        logger.info("✓ Cleared session data")
        
        # Clear employee access for current data
        employee_access_file = 'employee_access.json'
        if os.path.exists(employee_access_file):
            with open(employee_access_file, 'w') as f:
                json.dump([], f)
            logger.info("✓ Cleared employee access data")
        
        # Clear employee packages for current data
        employee_packages_file = 'employee_packages.json'
        if os.path.exists(employee_packages_file):
            with open(employee_packages_file, 'w') as f:
                json.dump([], f)
            logger.info("✓ Cleared employee packages data")
        
        # Clear submitted packages
        submitted_packages_file = 'submitted_packages.json'
        if os.path.exists(submitted_packages_file):
            with open(submitted_packages_file, 'w') as f:
                json.dump([], f)
            logger.info("✓ Cleared submitted packages")
        
        cleared_count = 0
        # Only clear current (non-archived) data
        if hasattr(package_builder, 'sap_uploads') and package_builder.sap_uploads:
            # Count current uploads before filtering
            cleared_count = len([u for u in package_builder.sap_uploads if not u.get('status', '').startswith('ARCHIVED')])
            # Keep only archived uploads
            package_builder.sap_uploads = [u for u in package_builder.sap_uploads if u.get('status', '').startswith('ARCHIVED')]
            package_builder.save_data()
            logger.info(f"✓ Cleared {cleared_count} current SAP upload(s) (preserved archived)")
        else:
            logger.info("- No current uploads to clear")
        
        # Optionally delete current (non-archived) uploaded files
        uploads_dir = 'uploads'
        files_deleted = 0
        if os.path.exists(uploads_dir):
            for file in os.listdir(uploads_dir):
                file_path = os.path.join(uploads_dir, file)
                # Check if file is not from an archived upload
                is_current = True
                if hasattr(package_builder, 'sap_uploads'):
                    for upload in package_builder.sap_uploads:
                        if file in upload.get('filename', '') and upload.get('status', '').startswith('ARCHIVED'):
                            is_current = False
                            break
                
                if is_current and (file.startswith('randwater_sap_data_') or file.startswith('randwater_export_')):
                    os.remove(file_path)
                    files_deleted += 1
            logger.info(f"✓ Deleted {files_deleted} current file(s) (preserved archived)")
        else:
            logger.info("- No uploads directory to clear")
        
        logger.info(f"=== CURRENT DATA CLEARED SUCCESSFULLY ===")
        logger.info(f"")
        
        # Save to system logs
        save_system_log({
            'action': 'CLEAR_DATA',
            'user': current_user,
            'timestamp': clear_timestamp,
            'details': {
                'uploads_cleared': cleared_count,
                'files_deleted': files_deleted
            }
        })
        
        return jsonify({
            'success': True, 
            'message': f'Cleared {cleared_count} current upload(s). Archived data preserved.'
        })
        
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        return jsonify({'error': f'Failed to clear data: {str(e)}'}), 500

@app.route('/api/system-logs')
def api_system_logs():
    """API endpoint to get system logs"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    logs = load_system_logs()
    # Reverse to show newest first
    logs.reverse()
    
    return jsonify(logs)

@app.route('/api/send-employee-credentials', methods=['POST'])
def send_employee_credentials():
    """Send login credentials to selected employees via email"""
    debug_info = []
    debug_info.append("=== SEND EMPLOYEE CREDENTIALS DEBUG START ===")
    
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        debug_info.append("Unauthorized access attempt")
        return jsonify({'error': 'Unauthorized', 'debug': debug_info}), 401
    
    try:
        data = request.get_json()
        debug_info.append(f"Request data: {data}")
        employees = data.get('employees', [])
        debug_info.append(f"Employees to send to: {employees}")
        
        if not employees:
            debug_info.append("No employees selected")
            return jsonify({'error': 'No employees selected', 'debug': debug_info}), 400
        
        sent_count = 0
        failed_emails = []
        
        # Load employee access data to get passwords
        try:
            with open('employee_access.json', 'r') as f:
                employee_access = json.load(f)
            debug_info.append(f"Loaded {len(employee_access)} employee access records")
        except Exception as e:
            debug_info.append(f"Failed to load employee access: {e}")
            employee_access = []
        
        for emp in employees:
            employee_id = emp['employee_id']
            email = emp['email']
            first_name = emp['first_name']
            surname = emp['surname']
            debug_info.append(f"Processing employee {employee_id}: {first_name} {surname} ({email})")
            
            # Find employee access record to get username and password
            access_record = next((acc for acc in employee_access if acc['employee_id'] == employee_id), None)
            
            if not access_record:
                debug_info.append(f"No access record found for employee {employee_id}")
                logger.warning(f"No access record found for employee {employee_id}")
                failed_emails.append(f"{employee_id} - No access record")
                continue
            
            username = access_record.get('username', employee_id)
            password = access_record.get('password', 'N/A')
            debug_info.append(f"Found credentials: username={username}, password={'*' * len(password) if password != 'N/A' else 'N/A'}")
            
            # Send email
            try:
                subject = "Rand Water Package Builder - Login Credentials"
                html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
        .credentials {{ background: #e8f4fd; border: 2px solid #2a5298; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .credential-item {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #2a5298; }}
        .value {{ font-family: monospace; background: white; padding: 5px 10px; border-radius: 4px; }}
        .instructions {{ background: white; border-left: 4px solid #2a5298; padding: 20px; margin: 20px 0; }}
        .instructions ol {{ margin: 10px 0; padding-left: 20px; }}
        .instructions li {{ margin: 8px 0; }}
        .login-button {{ display: inline-block; background: #2a5298; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 15px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🎯 Rand Water Package Builder</h2>
            <p>Your login credentials have been activated</p>
        </div>
        
        <div class="content">
            <p>Dear <strong>{first_name} {surname}</strong>,</p>
            
            <p>Welcome to the Rand Water Package Builder! Your access has been successfully activated and you can now log in to review and customize your compensation package.</p>
            
            <div class="credentials">
                <h3>🔑 Your Login Credentials</h3>
                <div class="credential-item">
                    <span class="label">Username:</span> <span class="value">{username}</span>
                </div>
                <div class="credential-item">
                    <span class="label">Password:</span> <span class="value">{password}</span>
                </div>
                <div class="credential-item">
                    <span class="label">Login URL:</span> 
                    <a href="http://localhost:5001/login" class="login-button">Access Package Builder</a>
                </div>
            </div>
            
            <div class="instructions">
                <h3>📋 Next Steps</h3>
                <ol>
                    <li>Click the "Access Package Builder" button above or visit: <a href="http://localhost:5001/login">http://localhost:5001/login</a></li>
                    <li>Enter your username and password</li>
                    <li>Review your current compensation package</li>
                    <li>Make any desired changes within your TCTC limit</li>
                    <li>Submit your package when ready</li>
                </ol>
            </div>
            
            <div class="warning">
                <strong>⏰ Important:</strong> Your access will expire in 30 days or upon package submission, whichever comes first.
            </div>
            
            <p>If you have any questions or need assistance, please contact your HR administrator.</p>
            
            <div class="footer">
                <p>Best regards,<br>
                <strong>Rand Water HR Team</strong></p>
                <p><em>This is an automated message. Please do not reply to this email.</em></p>
            </div>
        </div>
    </div>
</body>
</html>
                """
                
                text_body = f"""
Dear {first_name} {surname},

Your login credentials for the Rand Water Package Builder have been activated.

LOGIN CREDENTIALS:
==================
Username: {username}
Password: {password}
Login URL: http://localhost:5001/login

INSTRUCTIONS:
=============
1. Go to the login page using the URL above
2. Enter your username and password
3. Review your current compensation package
4. Make any desired changes within your TCTC limit
5. Submit your package when ready

IMPORTANT: Your access will expire in 30 days or upon package submission.

If you have any questions, please contact your HR administrator.

Best regards,
Rand Water HR Team
                """
                
                debug_info.append(f"Attempting to send email to {email}")
                success = send_email(subject, email, html_body, text_body)
                if success:
                    sent_count += 1
                    debug_info.append(f"Email sent successfully to {employee_id} ({email})")
                    logger.info(f"Sent credentials to {employee_id} ({email})")
                else:
                    debug_info.append(f"Email failed to send to {employee_id} ({email})")
                    failed_emails.append(f"{employee_id} - Email send failed")
                
            except Exception as e:
                debug_info.append(f"Exception sending email to {employee_id}: {str(e)}")
                logger.error(f"Failed to send email to {employee_id}: {str(e)}")
                failed_emails.append(f"{employee_id} - {str(e)}")
        
        debug_info.append(f"=== SEND EMPLOYEE CREDENTIALS DEBUG END ===")
        debug_info.append(f"Sent: {sent_count}, Failed: {len(failed_emails)}")
        
        if sent_count == 0:
            return jsonify({'error': 'Failed to send any emails', 'details': failed_emails, 'debug': debug_info}), 400
        elif failed_emails:
            return jsonify({'message': f'Sent {sent_count} emails successfully', 'warnings': failed_emails, 'debug': debug_info}), 200
        else:
            return jsonify({'message': f'Successfully sent {sent_count} emails', 'debug': debug_info}), 200
            
    except Exception as e:
        debug_info.append(f"=== SEND EMPLOYEE CREDENTIALS ERROR ===")
        debug_info.append(f"Error type: {type(e).__name__}")
        debug_info.append(f"Error message: {str(e)}")
        import traceback
        debug_info.append(f"Traceback: {traceback.format_exc()}")
        logger.error(f"Send employee credentials failed: {e}")
        return jsonify({'error': 'Failed to send emails', 'details': str(e), 'debug': debug_info}), 500
        save_system_log({
            'action': 'EMAIL_CREDENTIALS',
            'user': current_user,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'details': {
                'sent_count': sent_count,
                'failed_count': len(failed_emails),
                'recipients': [f"{e['employee_id']} ({e['email']})" for e in employees]
            }
        })
        
        if sent_count > 0:
            return jsonify({
                'success': True,
                'sent_count': sent_count,
                'failed_count': len(failed_emails),
                'failed_emails': failed_emails
            })
        else:
            return jsonify({'error': 'Failed to send any emails', 'details': failed_emails}), 500
            
    except Exception as e:
        logger.error(f"Error sending employee credentials: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
                         employees=active_employees,
                         active_employees=active_employees)

@app.route('/manage_packages')
def manage_packages():
    """Rand Water Admin - Package management interface"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    # Get packages from uploaded SAP data - always use active employees for consistency
    active_employees = get_active_randwater_employees()
    
    # Always convert employees to package format to ensure correct structure
    if active_employees:
        packages = []
        for emp in active_employees:
            package = {
                'employee_id': emp['employee_id'],
                'employee_name': f"{emp.get('first_name', '')} {emp.get('surname', '')}".strip(),
                'first_name': emp.get('first_name', ''),
                'surname': emp.get('surname', ''),
                'grade_band': emp.get('grade_band', ''),
                'department': emp.get('department', ''),
                'basic_salary': emp.get('basic_salary', 0),
                'current_tctc': emp.get('ctc', 0),  # Template expects current_tctc
                'tctc_limit': emp.get('ctc', 0) * 1.1,  # 10% buffer above current
                'ctc': emp.get('ctc', 0),
                'status': 'PENDING' if not emp.get('package_submitted', False) else 'COMPLETED',
                'is_submitted': emp.get('package_submitted', False),
                'submission_date': emp.get('access_granted', ''),
                'access_expires': emp.get('access_expires', ''),
                'access_status': 'EXPIRED' if emp.get('is_expired', False) else 'ACTIVE',
                'package_submitted': emp.get('package_submitted', False)
            }
            packages.append(package)
    else:
        packages = []
    
    logger.info(f"Loaded {len(packages)} packages for management")
    
    return render_template('manage_packages.html', 
                         config=RANDWATER_CONFIG, 
                         packages=packages,
                         total_packages=len(packages))

@app.route('/package_view/<employee_id>')
def package_view(employee_id):
    """Rand Water Admin - View package details with edit capabilities"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        # Get employee data
        active_employees = get_active_randwater_employees()
        employee = None
        for emp in active_employees:
            if emp['employee_id'] == employee_id:
                employee = emp
                break
        
        if not employee:
            return redirect(url_for('manage_packages'))
        
        # Get audit trail for this package
        audit_trail = get_package_audit_trail(employee_id)
        
        # Admin view - no notifications (notifications are for employee login only)
        # Get notifications for this employee (only if this is an employee viewing their own package)
        notifications = []  # Admin shouldn't see employee notifications
        
        return render_template('package_view_edit.html', 
                             config=RANDWATER_CONFIG,
                             employee=employee,
                             audit_trail=audit_trail,
                             notifications=notifications)
        
    except Exception as e:
        logger.error(f"Error viewing package for {employee_id}: {str(e)}")
        return redirect(url_for('manage_packages'))

@app.route('/package_edit/<employee_id>', methods=['POST'])
def package_edit(employee_id):
    """Rand Water Admin - Save package edits with audit trail"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get the changes from the request
        changes = request.get_json()
        admin_user = session.get('user', 'Unknown Admin')
        
        # Save the changes with audit trail
        result = save_package_changes(employee_id, changes, admin_user)
        
        if result['success']:
            # Create notification for employee
            create_employee_notification(
                employee_id, 
                f"Your compensation package has been updated by {admin_user}",
                admin_user
            )
            
            # Get updated package data to return
            updated_package = get_employee_package_data(employee_id)
            
            return jsonify({
                'success': True, 
                'message': 'Package updated successfully',
                'updated_data': updated_package
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error saving package changes for {employee_id}: {str(e)}")
        return jsonify({'error': 'Failed to save changes'}), 500

@app.route('/export_packages_for_sap')
def export_packages_for_sap():
    """Rand Water Admin - Export packages for SAP"""
    try:
        if not session.get('admin') and not session.get('isRandWaterAdmin'):
            return redirect(url_for('randwater_admin_login'))
        
        logger.info("=== EXPORT PACKAGES DEBUG START ===")
        logger.info(f"Session admin: {session.get('admin')}")
        logger.info(f"Session isRandWaterAdmin: {session.get('isRandWaterAdmin')}")
        # Get the latest SAP upload file
        sap_uploads = load_sap_uploads()
        logger.info(f"Found {len(sap_uploads)} SAP uploads")
        
        original_file_path = None
        
        if sap_uploads:
            # Get the most recent upload
            latest_upload = max(sap_uploads, key=lambda x: x['upload_date'])
            logger.info(f"Latest upload: {latest_upload}")
            original_file_path = os.path.join('uploads', latest_upload['filename'])
            logger.info(f"Original file path: {original_file_path}")
            
            if not os.path.exists(original_file_path):
                logger.warning(f"SAP file not found: {original_file_path}")
                original_file_path = None
        
        # If no uploaded SAP file, use sample data
        if not original_file_path:
            logger.info("No SAP uploads found, using sample data for export")
            original_file_path = 'sample_randwater_sap_data.xlsx'
            logger.info(f"Using sample file: {original_file_path}")
            
            if not os.path.exists(original_file_path):
                logger.error("Sample SAP file not found")
                return jsonify({'error': 'No SAP data available for export.'}), 400
        
        logger.info(f"Final file path: {original_file_path}")
        
        # Read the original SAP file
        import pandas as pd
        logger.info("Reading Excel file with pandas...")
        original_df = pd.read_excel(original_file_path)
        logger.info(f"Successfully read Excel file with {len(original_df)} rows and {len(original_df.columns)} columns")
        
        # Get submitted packages from submitted_packages.json
        submitted_packages = []
        if os.path.exists('submitted_packages.json'):
            try:
                with open('submitted_packages.json', 'r') as f:
                    submitted_packages = json.load(f)
                    # Filter only those with status 'submitted'
                    submitted_packages = [p for p in submitted_packages if p.get('status') == 'submitted']
                    logger.info(f"Found {len(submitted_packages)} submitted packages to export")
            except Exception as e:
                logger.warning(f"Could not load submitted packages: {e}")
                submitted_packages = []
        
        # Create a copy of the original data
        export_df = original_df.copy()
        
        # Update the data with submitted package values (if any)
        if submitted_packages:
            for package in submitted_packages:
                employee_id = package['employee_id']
                package_data = package.get('package_components', {})
                
                # Find the row for this employee
                employee_row = export_df[export_df['EMPLOYEECODE'] == employee_id]
                if not employee_row.empty:
                    row_index = employee_row.index[0]
                    
                    # Update the salary components with values from submitted package
                    # Use the EXACT values that were agreed upon, not recalculated ones
                    
                    # Get values for calculations
                    tpe_value = package_data.get('tpe') or package_data.get('basic_salary', 0)
                    tpe_value = float(tpe_value)
                    
                    # Update TPE column with the saved TPE value
                    export_df.at[row_index, 'TPE'] = tpe_value
                    
                    # Calculate cash component if not saved (for packages submitted before the update)
                    cash_component = package_data.get('cash_component')
                    if cash_component is None or cash_component == 0:
                        # Recalculate cash component from saved values
                        car_value = float(package_data.get('car_allowance', 0))
                        housing_value = float(export_df.at[row_index, 'HOUSING'])
                        medical_er = float(export_df.at[row_index, 'MEDICALERCONTRIBUTION'])
                        
                        # Get pension and group life values from submitted data or original
                        pension_er = float(package_data.get('pension_er', export_df.at[row_index, 'PENSIONERCONTRIBUTION']))
                        group_life_er = float(package_data.get('group_life_er', export_df.at[row_index, 'GROUPLIFEERCONTRIBUTION']))
                        bonus_value = float(package_data.get('bonus', export_df.at[row_index, 'BONUSPROVISION']))
                        
                        # Cash = CTC - Car - Housing - Pension ER - Medical ER - Group Life ER - Bonus
                        tctc = float(export_df.at[row_index, 'TCTC'])
                        cash_component = tctc - car_value - housing_value - pension_er - medical_er - group_life_er - bonus_value
                    
                    # Update IT08_Type1Value column with the calculated cash component (CASH column stays 0)
                    if 'IT08_Type1Value' in export_df.columns:
                        export_df.at[row_index, 'IT08_Type1Value'] = float(cash_component)
                    
                    # Update car allowance
                    if 'car_allowance' in package_data:
                        export_df.at[row_index, 'CAR'] = float(package_data['car_allowance'])
                    
                    # Use the saved calculated pension values
                    if 'pension_ee' in package_data:
                        export_df.at[row_index, 'PENSIONEECONTRIBUTION'] = float(package_data['pension_ee'])
                    if 'pension_er' in package_data:
                        export_df.at[row_index, 'PENSIONERCONTRIBUTION'] = float(package_data['pension_er'])
                    
                    # Use the saved calculated group life values
                    if 'group_life_ee' in package_data:
                        export_df.at[row_index, 'GROUPLIFEEECONTRIBUTION'] = float(package_data['group_life_ee'])
                    if 'group_life_er' in package_data:
                        export_df.at[row_index, 'GROUPLIFEERCONTRIBUTION'] = float(package_data['group_life_er'])
                    
                    if 'housing_allowance' in package_data:
                        export_df.at[row_index, 'HOUSING'] = float(package_data['housing_allowance'])
                    
                    if 'bonus' in package_data:
                        export_df.at[row_index, 'BONUSPROVISION'] = float(package_data['bonus'])
                    
                    if 'cellphone_allowance' in package_data:
                        export_df.at[row_index, 'CELLPHONEALLOWANCE'] = float(package_data['cellphone_allowance'])
                    
                    if 'data_service_allowance' in package_data:
                        export_df.at[row_index, 'DATASERVICEALLOWANCE'] = float(package_data['data_service_allowance'])
                    
                    # Get values for TCTC calculation
                    car_value = package_data.get('car_allowance', 0) or float(export_df.at[row_index, 'CAR'])
                    housing_value = package_data.get('housing_allowance', 0) or float(export_df.at[row_index, 'HOUSING'])
                    medical_value = float(export_df.at[row_index, 'MEDICALERCONTRIBUTION'])
                    pension_er = float(package_data.get('pension_er', export_df.at[row_index, 'PENSIONERCONTRIBUTION']))
                    group_life_er = float(package_data.get('group_life_er', export_df.at[row_index, 'GROUPLIFEERCONTRIBUTION']))
                    bonus_value = package_data.get('bonus', 0) or float(export_df.at[row_index, 'BONUSPROVISION'])
                    cellphone_value = package_data.get('cellphone_allowance', 0) or float(export_df.at[row_index, 'CELLPHONEALLOWANCE'])
                    data_service_value = package_data.get('data_service_allowance', 0) or float(export_df.at[row_index, 'DATASERVICEALLOWANCE'])
                    
                    # Recalculate TCTC based on updated values
                    tctc = (
                        tpe_value +
                        car_value +
                        housing_value +
                        pension_er +
                        medical_value +
                        bonus_value +
                        cellphone_value +
                        data_service_value
                    )
                    export_df.at[row_index, 'TCTC'] = tctc
            
            # Filter to only include submitted employees
            submitted_employee_ids = [p['employee_id'] for p in submitted_packages]
            export_df = export_df[export_df['EMPLOYEECODE'].isin(submitted_employee_ids)]
            logger.info(f"Filtered export to {len(export_df)} employees (submitted packages only)")
        
        else:
            logger.info("No submitted packages found")
            # Return error if no packages to export
            return jsonify({'error': 'No submitted packages to export'}), 400
        
        # Generate export filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_filename = f'randwater_export_{timestamp}.xlsx'
        export_path = os.path.join('uploads', export_filename)
        
        logger.info(f"Generating export file: {export_filename}")
        logger.info(f"Export path: {export_path}")
        
        # Save the updated Excel file
        logger.info("Saving Excel file...")
        export_df.to_excel(export_path, index=False)
        logger.info(f"Excel file saved successfully to: {export_path}")
        
        # Log the export
        logger.info(f"Exported {len(submitted_packages)} submitted packages to {export_filename}")
        
        # Return the file for download
        logger.info("Returning file for download...")
        return send_file(export_path, as_attachment=True, download_name=export_filename)
        
    except Exception as e:
        logger.error(f"Error exporting packages: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'message': f'Export failed: {str(e)}'
        }), 500

@app.route('/package_analytics')
def package_analytics():
    """Rand Water Admin - Package analytics and reporting"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        # Get all submitted packages
        submitted_packages = []
        if os.path.exists('submitted_packages.json'):
            with open('submitted_packages.json', 'r') as f:
                submitted_packages = json.load(f)
        
        # Get all employees with access
        employee_data = []
        if os.path.exists('employee_access.json'):
            with open('employee_access.json', 'r') as f:
                employee_data = json.load(f)
        
        # Get all employee packages (including drafts)
        all_packages = []
        draft_packages = []
        
        # Load submitted packages
        for pkg in submitted_packages:
            if pkg.get('status') == 'submitted':
                all_packages.append(pkg)
        
        # Load draft packages
        if os.path.exists('drafts'):
            for filename in os.listdir('drafts'):
                if filename.startswith('package_') and filename.endswith('.json'):
                    try:
                        with open(os.path.join('drafts', filename), 'r') as f:
                            draft = json.load(f)
                            draft['status'] = 'draft'
                            draft_packages.append(draft)
                            all_packages.append(draft)
                    except Exception as e:
                        logger.warning(f"Could not load draft {filename}: {e}")
        
        # Calculate analytics
        total_packages = len(all_packages)
        submitted_count = len([p for p in all_packages if p.get('status') == 'submitted'])
        draft_count = len([p for p in all_packages if p.get('status') == 'draft'])
        pending_count = len(employee_data) - total_packages
        
        # TCTC statistics
        tctc_values = []
        for pkg in all_packages:
            components = pkg.get('package_components', {})
            if components:
                tctc = (
                    float(components.get('tpe', 0)) +
                    float(components.get('car_allowance', 0)) +
                    float(components.get('housing_allowance', 0)) +
                    float(components.get('cellphone_allowance', 0)) +
                    float(components.get('data_service_allowance', 0)) +
                    float(components.get('cash_component', 0)) +
                    float(components.get('bonus', 0)) +
                    float(components.get('pension_er', 0)) +
                    float(components.get('medical_er', 0)) +
                    float(components.get('group_life_er', 0))
                )
                tctc_values.append(tctc)
        
        avg_tctc = sum(tctc_values) / len(tctc_values) if tctc_values else 0
        min_tctc = min(tctc_values) if tctc_values else 0
        max_tctc = max(tctc_values) if tctc_values else 0
        
        # Grade band distribution
        grade_counts = {}
        for emp in employee_data:
            grade = emp.get('grade_band', 'Unknown')
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        # Department distribution
        dept_counts = {}
        for emp in employee_data:
            dept = emp.get('department', 'Unknown')
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        
        analytics = {
            'total_packages': total_packages,
            'submitted_packages': submitted_count,
            'draft_packages': draft_count,
            'pending_packages': max(0, pending_count),
            'total_employees': len(employee_data),
            'avg_tctc': avg_tctc,
            'min_tctc': min_tctc,
            'max_tctc': max_tctc,
            'tctc_range': {
                'min': min_tctc,
                'max': max_tctc
            },
            'grade_distribution': grade_counts,
            'department_distribution': dept_counts,
            'tctc_values': tctc_values
        }
        
        return render_template('package_analytics.html', 
                             analytics=analytics,
                             config=RANDWATER_CONFIG)
    
    except Exception as e:
        logger.error(f"Error in package_analytics: {e}")
        logger.exception("Full error:")
        # Return error page with details instead of redirecting
        return f"""
        <html>
        <head><title>Analytics Error</title></head>
        <body style="font-family: Arial; padding: 50px;">
            <h2>Error Loading Analytics</h2>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><strong>Type:</strong> {type(e).__name__}</p>
            <hr>
            <a href="{url_for('randwater_admin_panel')}">← Back to Dashboard</a>
        </body>
        </html>
        """

# ============================================================================
# REPORTING ROUTES
# ============================================================================

@app.route('/payslip_reports')
def payslip_reports():
    """Bulk Payslip Reports with filters"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        # Get all employees for filter options
        employee_data = []
        if os.path.exists('employee_access.json'):
            with open('employee_access.json', 'r') as f:
                employee_data = json.load(f)
        
        # Get unique grade bands
        grade_bands = list(set([emp.get('grade_band', 'Unknown') for emp in employee_data]))
        grade_bands.sort()
        
        # Get unique departments
        departments = list(set([emp.get('department', 'Unknown') for emp in employee_data]))
        departments.sort()
        
        return render_template('payslip_reports.html',
                             employees=employee_data,
                             grade_bands=grade_bands,
                             departments=departments,
                             config=RANDWATER_CONFIG)
    except Exception as e:
        logger.error(f"Error loading payslip reports: {e}")
        return f"Error: {str(e)}"

@app.route('/tax_reports')
def tax_reports():
    """Bulk Tax Reports with filters"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        # Get all employees for filter options
        employee_data = []
        if os.path.exists('employee_access.json'):
            with open('employee_access.json', 'r') as f:
                employee_data = json.load(f)
        
        # Get unique grade bands
        grade_bands = list(set([emp.get('grade_band', 'Unknown') for emp in employee_data]))
        grade_bands.sort()
        
        return render_template('tax_reports.html',
                             employees=employee_data,
                             grade_bands=grade_bands,
                             config=RANDWATER_CONFIG)
    except Exception as e:
        logger.error(f"Error loading tax reports: {e}")
        return f"Error: {str(e)}"

@app.route('/variance_dashboard')
def variance_dashboard():
    """Variance Dashboard - Compare package changes"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        return render_template('variance_dashboard.html',
                             config=RANDWATER_CONFIG)
    except Exception as e:
        logger.error(f"Error loading variance dashboard: {e}")
        return f"Error: {str(e)}"

@app.route('/audit_trail')
def audit_trail():
    """Full Audit Trail Report"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        # Load audit log
        audit_logs = []
        if os.path.exists('randwater_package_audit.json'):
            with open('randwater_package_audit.json', 'r') as f:
                audit_logs = json.load(f)
        
        # Sort by timestamp (newest first)
        audit_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return render_template('audit_trail.html',
                             audit_logs=audit_logs,
                             config=RANDWATER_CONFIG)
    except Exception as e:
        logger.error(f"Error loading audit trail: {e}")
        return f"Error: {str(e)}"

@app.route('/system_config_report')
def system_config_report():
    """System Configuration Report - View Only"""
    if not session.get('admin') and not session.get('isRandWaterAdmin') and not session.get('isSuperAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        # Load all configuration data
        tax_settings = load_tax_settings()
        
        # Load pension config
        pension_config = {}
        if os.path.exists('pension_config.json'):
            with open('pension_config.json', 'r') as f:
                pension_config = json.load(f)
        else:
            # Default pension options from Rand Water Provident Fund
            pension_config = {
                'A': {'employee_contribution': 8.67, 'employer_contribution': 17.19},
                'B': {'employee_contribution': 8.67, 'employer_contribution': 17.19},
                'C': {'employee_contribution': 8.67, 'employer_contribution': 9.45},
                'D': {'employee_contribution': 8.67, 'employer_contribution': 17.19},
                'E': {'employee_contribution': 8.67, 'employer_contribution': 17.19},
                'F': {'employee_contribution': 8.67, 'employer_contribution': 17.19},
                'G': {'employee_contribution': 8.67, 'employer_contribution': 17.19},
                'SAMWU': {'employee_contribution': 7.5, 'employer_contribution': 7.5}
            }
        
        # Load medical aid configuration if exists
        medical_config = {}
        if os.path.exists('medical_config.json'):
            with open('medical_config.json', 'r') as f:
                medical_config = json.load(f)
        
        config_data = {
            'tax_settings': tax_settings,
            'pension_config': pension_config,
            'medical_config': medical_config,
            'randwater_config': RANDWATER_CONFIG,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return render_template('system_config_report.html',
                             config_data=config_data,
                             config=RANDWATER_CONFIG)
    except Exception as e:
        logger.error(f"Error loading system config report: {e}")
        return f"Error: {str(e)}"

@app.route('/export_payslips_pdf', methods=['POST'])
def export_payslips_pdf():
    """Export selected employee payslips to PDF"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.units import inch
        import io
        
        employee_ids = request.form.getlist('employee_ids[]')
        
        if not employee_ids:
            return "No employees selected", 400
        
        # Create PDF in memory
        buffer = io.BytesIO()
        c = pdf_canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        for emp_id in employee_ids:
            # Get employee data
            active_employees = get_active_randwater_employees()
            employee = next((e for e in active_employees if e['employee_id'] == emp_id), None)
            
            if not employee:
                continue
            
            # Draw payslip
            y = height - 1*inch
            
            # Header
            c.setFont("Helvetica-Bold", 16)
            c.drawString(1*inch, y, "Rand Water - Employee Payslip")
            y -= 0.5*inch
            
            c.setFont("Helvetica", 10)
            c.drawString(1*inch, y, f"Employee ID: {employee['employee_id']}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"Name: {employee.get('first_name', '')} {employee.get('surname', '')}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"Grade Band: {employee.get('grade_band', 'N/A')}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"Department: {employee.get('department', 'N/A')}")
            y -= 0.5*inch
            
            # Earnings
            c.setFont("Helvetica-Bold", 12)
            c.drawString(1*inch, y, "Earnings")
            y -= 0.3*inch
            c.setFont("Helvetica", 10)
            c.drawString(1*inch, y, f"Basic Salary: R {employee.get('basic_salary', 0):,.2f}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"Total CTC: R {employee.get('ctc', 0):,.2f}")
            y -= 0.5*inch
            
            # Add more payslip details as needed
            
            # Next page for next employee
            c.showPage()
        
        # Save PDF
        c.save()
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'payslips_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error exporting payslips: {e}")
        return f"Error: {str(e)}", 500

@app.route('/export_tax_report_pdf')
def export_tax_report_pdf():
    """Export tax report to PDF"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    return "Tax report PDF generation coming soon", 200

@app.route('/export_variance_csv')
def export_variance_csv():
    """Export variance report to CSV"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Employee ID', 'Name', 'Original CTC', 'New CTC', 'Variance', '% Change', 'Status'])
        
        # Sample data - replace with actual variance data
        writer.writerow(['RW001', 'John Doe', '500000', '525000', '25000', '5.0%', 'Submitted'])
        writer.writerow(['RW003', 'Jane Smith', '600000', '650000', '50000', '8.3%', 'Submitted'])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            as_attachment=True,
            download_name=f'variance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting variance: {e}")
        return f"Error: {str(e)}", 500

@app.route('/export_audit_trail_csv')
def export_audit_trail_csv():
    """Export audit trail to CSV"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import io
        import csv
        
        # Load audit log
        audit_logs = []
        if os.path.exists('randwater_package_audit.json'):
            with open('randwater_package_audit.json', 'r') as f:
                audit_logs = json.load(f)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Timestamp', 'User', 'Action', 'Employee ID', 'Description'])
        
        # Write data
        for log in audit_logs:
            writer.writerow([
                log.get('timestamp', ''),
                log.get('admin_username', 'System'),
                log.get('action', ''),
                log.get('employee_id', ''),
                log.get('description', '')
            ])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            as_attachment=True,
            download_name=f'audit_trail_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting audit trail: {e}")
        return f"Error: {str(e)}", 500

@app.route('/save_simulation', methods=['POST'])
def save_simulation():
    """Save salary simulation"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        simulation_data = request.get_json()
        
        # Save to file
        simulations_file = 'salary_simulations.json'
        simulations = []
        
        if os.path.exists(simulations_file):
            with open(simulations_file, 'r') as f:
                simulations = json.load(f)
        
        # Remove existing simulation with same ID
        simulations = [s for s in simulations if s.get('id') != simulation_data.get('id')]
        
        # Add new simulation
        simulations.append(simulation_data)
        
        # Save back to file
        with open(simulations_file, 'w') as f:
            json.dump(simulations, f, indent=2)
        
        logger.info(f"Saved simulation: {simulation_data.get('id')}")
        return jsonify({'success': True, 'message': 'Simulation saved successfully'})
        
    except Exception as e:
        logger.error(f"Error saving simulation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_saved_simulations')
def get_saved_simulations():
    """Get all saved simulations"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        simulations_file = 'salary_simulations.json'
        simulations = []
        
        if os.path.exists(simulations_file):
            with open(simulations_file, 'r') as f:
                simulations = json.load(f)
        
        return jsonify({'success': True, 'simulations': simulations})
        
    except Exception as e:
        logger.error(f"Error loading simulations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/variance_data')
def get_variance_data():
    """Get variance data for dashboard"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Sample variance data
    data = {
        'totalEmployees': 3,
        'modifiedPackages': 2,
        'avgChange': 5.2,
        'totalVariance': 125000,
        'employees': [
            {
                'employee_id': 'RW001',
                'name': 'John Baloyi',
                'originalCTC': 500000,
                'newCTC': 525000,
                'variance': 25000,
                'percentChange': 5.0,
                'status': 'Submitted'
            },
            {
                'employee_id': 'RW003',
                'name': 'David Malecki',
                'originalCTC': 600000,
                'newCTC': 650000,
                'variance': 50000,
                'percentChange': 8.3,
                'status': 'Submitted'
            }
        ]
    }
    
    return jsonify(data)

@app.route('/admin/randwater/employee-details/<employee_id>')
def employee_details(employee_id):
    """Rand Water Admin - Get employee details for modal"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get real employee data from the uploaded SAP file
        active_employees = get_active_randwater_employees()
        logger.info(f"Found {len(active_employees)} active employees")
        logger.info(f"Looking for employee ID: {employee_id}")
        
        # Find the specific employee
        employee = None
        for emp in active_employees:
            if emp['employee_id'] == employee_id:
                employee = emp
                logger.info(f"Found employee: {emp}")
                break
        
        if not employee:
            return jsonify({'error': f'Employee {employee_id} not found'}), 404
        
        # Calculate current package status
        package_status = 'Pending' if not employee.get('package_submitted', False) else 'Completed'
        
        # Calculate actual net pay (basic calculation)
        basic_salary = employee.get('basic_salary', 0)
        estimated_deductions = basic_salary * 0.25  # Rough estimate of 25% deductions
        estimated_net_pay = basic_salary - estimated_deductions
        
        employee_data = {
            'success': True,
            'employee': {
                'employee_id': employee['employee_id'],
                'username': employee['employee_id'].lower(),
                'password': 'TempPass123',  # Default password - will be customizable
                'first_name': employee.get('first_name', ''),
                'surname': employee.get('surname', ''),
                'grade_band': employee.get('grade_band', 'O-Q'),
                'department': employee.get('department', 'General'),
                'job_title': employee.get('job_title', 'Employee'),
                'status': 'EXPIRED' if employee.get('is_expired', False) else 'ACTIVE',
                'access_granted': employee.get('access_granted'),
                'access_expires': employee.get('access_expires'),
                'days_remaining': employee.get('days_remaining', 0),
                'last_login': None,  # Can be enhanced later
                'package_submitted': employee.get('package_submitted', False),
                'submission_date': None  # Can be enhanced later
            },
            'package': {
                'basic_salary': basic_salary,
                'total_earnings': basic_salary,  # Will be calculated properly in payslip
                'total_deductions': estimated_deductions,
                'net_pay': estimated_net_pay,
                'ctc': employee.get('ctc', 0),
                'status': package_status
            }
        }

        logger.info(f"Returning employee data: {employee_data}")
        return jsonify(employee_data)
        
    except Exception as e:
        logger.error(f"Error getting employee details: {str(e)}")
        logger.exception("Full exception details:")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/randwater/employee-payslip/<employee_id>')
def employee_payslip(employee_id):
    """Rand Water Admin - Get employee payslip data from uploaded SAP file"""
    # Allow both admins and employees (employees can only view their own payslip)
    is_admin = session.get('admin') or session.get('isRandWaterAdmin')
    is_employee = session.get('employee_id') == employee_id
    
    if not is_admin and not is_employee:
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
        # Priority order: 1) Draft (if exists), 2) Submitted package, 3) Original SAP data
        package_components = {}
        
        # First check for draft
        draft_file = f'drafts/package_{employee_id}.json'
        if os.path.exists(draft_file):
            try:
                with open(draft_file, 'r') as f:
                    draft_data = json.load(f)
                    package_components = draft_data.get('package_components', {})
                    logger.info(f"Using DRAFT values for payslip {employee_id}")
            except Exception as e:
                logger.warning(f"Could not load draft: {e}")
        
        # If no draft, check for submitted package
        if not package_components:
            submitted_packages = []
            if os.path.exists('submitted_packages.json'):
                try:
                    with open('submitted_packages.json', 'r') as f:
                        submitted_packages = json.load(f)
                        submitted_packages = [p for p in submitted_packages if p.get('status') == 'submitted']
                except Exception as e:
                    logger.warning(f"Could not load submitted packages: {e}")
            
            submitted_package = None
            for pkg in submitted_packages:
                if pkg.get('employee_id') == employee_id:
                    submitted_package = pkg
                    package_components = pkg.get('package_components', {})
                    logger.info(f"Using SUBMITTED package values for payslip {employee_id}")
                    break
        
        # Try to get employee data from persistent storage first
        employee_row = None
        
        # First try to read from Excel file if it exists
        if session.get('last_upload'):
            filepath = session['last_upload']['filepath']
            
            if os.path.exists(filepath):
                try:
                    df = pd.read_excel(filepath)
                    # Find the employee in the uploaded data
                    for index, row in df.iterrows():
                        if 'EMPLOYEECODE' in df.columns and str(row['EMPLOYEECODE']) == str(employee_id):
                            employee_row = row
                            break
                except Exception as e:
                    logger.warning(f"Could not read Excel file for payslip: {str(e)}")
        
        # If Excel file not found or employee not found, use persistent storage
        if employee_row is None:
            try:
                recent_uploads = package_builder.sap_uploads
                if recent_uploads:
                    # Sort by upload date and get the most recent
                    recent_uploads.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
                    latest_upload = recent_uploads[0]
                    
                    if 'employee_data' in latest_upload:
                        # Find the employee in persistent storage
                        for emp_data in latest_upload['employee_data']:
                            if str(emp_data.get('EMPLOYEECODE', '')) == str(employee_id):
                                employee_row = emp_data
                                logger.info(f"Found employee {employee_id} in persistent storage for payslip")
                                break
            except Exception as e:
                logger.error(f"Error accessing persistent storage for payslip: {str(e)}")
        
        if employee_row is None:
            return jsonify({'error': f'Employee {employee_id} not found in uploaded SAP data'}), 404
        
        # package_components already loaded from draft/submitted above
        # If still empty, will use original SAP data as fallback
        
        payslip_data = {
            'success': True,
            'employee': {
                'employee_id': str(employee_row.get('EMPLOYEECODE', employee_id)),
                'first_name': str(employee_row.get('FIRSTNAME', '')),
                'surname': str(employee_row.get('SURNAME', '')),
                'grade_band': str(employee_row.get('BAND', 'O-Q')),
                'department': str(employee_row.get('DEPARTMENT', 'General')),
                'job_title': str(employee_row.get('JOBLONG', 'Employee')),
                'basic_salary': float(package_components.get('tpe', employee_row.get('TPE', 0))),
                'ctc': safe_float(employee_row.get('TCTC', 0))  # Use TCTC instead of CTC
            },
            'payslip': {
                # Use package_components (draft/submitted) if available, otherwise SAP data
                'tctc': safe_float(employee_row.get('TCTC', 0)),
                'tpe': float(package_components.get('tpe', employee_row.get('TPE', 0))),
                'car_allowance': float(package_components.get('car_allowance', employee_row.get('CAR', 0))),
                'cellphone_allowance': float(package_components.get('cellphone_allowance', employee_row.get('CELLPHONEALLOWANCE', 0))),
                'data_service_allowance': float(package_components.get('data_service_allowance', employee_row.get('DATASERVICEALLOWANCE', 0))),
                'housing_allowance': float(package_components.get('housing_allowance', employee_row.get('HOUSING', 0))),
                'critical_skills': safe_float(employee_row.get('CRITICALSKILLS', 0)),
                'cash_allowance': float(package_components.get('cash_component', employee_row.get('CASH', 0))),
                'bonus': float(package_components.get('bonus', employee_row.get('BONUSPROVISION', 0))),
                
                # Employee deductions - use package_components values if available
                'pension_employee': float(package_components.get('pension_ee', employee_row.get('PENSIONEECONTRIBUTION', 0))),
                'medical_employee': float(package_components.get('medical_ee', employee_row.get('MEDICALEECONTRIBUTION', 0))),
                'group_life_employee': float(package_components.get('group_life_ee', employee_row.get('GROUPLIFEEECONTRIBUTION', 0))),
                'uif_employee': safe_float(employee_row.get('UIF', 0)),
                
                # Employer contributions - use package_components values if available
                'pension_employer': float(package_components.get('pension_er', employee_row.get('PENSIONERCONTRIBUTION', 0))),
                'medical_employer': float(package_components.get('medical_er', employee_row.get('MEDICALERCONTRIBUTION', 0))),
                'group_life_employer': float(package_components.get('group_life_er', employee_row.get('GROUPLIFEERCONTRIBUTION', 0))),
                'uif_employer': safe_float(employee_row.get('UIF', 0)),  # Same as employee for UIF
                'development_levy': 0,  # Will be calculated
                
                # Tax - use saved tax if available (from draft/submitted)
                'tax': float(package_components.get('tax', 0)),
                'total_tax': float(package_components.get('tax', 0)),
                
                # Additional info for package breakdown (use ORIGINAL SAP values, not modifiable)
                'pension_option': str(employee_row.get('PENSIONOPTION', 'N/A')),
                'medical_provider': str(employee_row.get('MEDICAL', 'N/A')),
                'medical_option': str(employee_row.get('MEDICALOPTION', 'N/A')),
                'medical_dependents': int(safe_float(employee_row.get('SPOUSE', 0)) + safe_float(employee_row.get('CHILDREN', 0)) + safe_float(employee_row.get('ADULTS', 0)))
            }
        }
        
        # Calculate bonus provision (monthly amount deducted from package)
        bonus_provision_monthly = payslip_data['payslip']['bonus'] / 12 if payslip_data['payslip']['bonus'] > 0 else 0
        
        # Calculate total employer contributions
        total_employer_contributions = (
            payslip_data['payslip']['pension_employer'] + 
            payslip_data['payslip']['medical_employer'] + 
            payslip_data['payslip']['group_life_employer'] + 
            payslip_data['payslip']['uif_employer']
        )
        
        # Calculate Development Levy (1% of gross salary)
        gross_salary = payslip_data['payslip']['tpe'] + payslip_data['payslip']['car_allowance']
        payslip_data['payslip']['development_levy'] = round(gross_salary * 0.01, 2)
        total_employer_contributions += payslip_data['payslip']['development_levy']
        
        # GOLDEN RULE: CTC is FIXED - everything must add up to exactly the CTC
        # CTC = TPE + Housing + Employer Contributions + Bonus Provision + Car Allowance
        
        # Calculate Pensionable Salary (TPE) - Rand Water format
        # TPE = CTC - Housing - Employer Contributions - Bonus Provision - Car Allowance
        pensionable_salary = (
            payslip_data['payslip']['tctc'] - 
            payslip_data['payslip']['housing_allowance'] - 
            total_employer_contributions - 
            bonus_provision_monthly -
            payslip_data['payslip']['car_allowance']  # Car allowance is deducted from CTC
        )
        
        # Ensure TPE is not negative (safety check)
        pensionable_salary = max(0, pensionable_salary)
        
        payslip_data['payslip']['pensionable_salary'] = round(pensionable_salary, 2)
        
        # VERIFICATION: Ensure CTC constraint is maintained
        calculated_ctc = (
            payslip_data['payslip']['pensionable_salary'] + 
            payslip_data['payslip']['housing_allowance'] + 
            total_employer_contributions + 
            bonus_provision_monthly +
            payslip_data['payslip']['car_allowance']
        )
        
        # Log verification for debugging
        print(f"CTC Verification for {employee_id}:")
        print(f"  Original CTC: R {payslip_data['payslip']['tctc']:.2f}")
        print(f"  Calculated CTC: R {calculated_ctc:.2f}")
        print(f"  Difference: R {abs(payslip_data['payslip']['tctc'] - calculated_ctc):.2f}")
        
        # If there's a small rounding difference, adjust TPE to maintain CTC
        if abs(payslip_data['payslip']['tctc'] - calculated_ctc) > 0.01:
            adjustment = payslip_data['payslip']['tctc'] - calculated_ctc
            payslip_data['payslip']['pensionable_salary'] = round(payslip_data['payslip']['pensionable_salary'] + adjustment, 2)
            print(f"  Adjusted TPE by R {adjustment:.2f} to maintain CTC constraint")
        
        # Calculate total earnings = Cash + Car + Housing + Cellphone + Data Service
        # (TPE is only for pension calculation, not actual earnings)
        total_earnings = (
            payslip_data['payslip']['cash_allowance'] +
            payslip_data['payslip']['car_allowance'] +
            payslip_data['payslip']['housing_allowance'] +
            payslip_data['payslip']['cellphone_allowance'] +
            payslip_data['payslip']['data_service_allowance']
        )
        payslip_data['payslip']['total_earnings'] = round(total_earnings, 2)
        
        # Use saved UIF if available from package_components, otherwise calculate
        if 'uif' in package_components and package_components['uif'] > 0:
            payslip_data['payslip']['uif_employee'] = float(package_components['uif'])
        elif not payslip_data['payslip']['uif_employee'] or payslip_data['payslip']['uif_employee'] == 0:
            uif_rate = 0.01  # 1%
            uif_amount = min(total_earnings * uif_rate, 177.12)
            payslip_data['payslip']['uif_employee'] = round(uif_amount, 2)
        
        # If we have a saved tax value from package_components, use it directly
        if 'tax' in package_components and package_components['tax'] > 0:
            payslip_data['payslip']['tax'] = float(package_components['tax'])
            payslip_data['payslip']['total_tax'] = float(package_components['tax'])
            logger.info(f"Using SAVED tax value: R{package_components['tax']:.2f}")
        else:
            # Calculate tax using the CORRECT Rand Water calculation
            # Based on SARS 2024 tax tables with complete rebates and medical credits
            
            # 1. Calculate Taxable Income (Monthly)
            # Taxable Income = Cash Component + Car Allowance (80%) + Housing Allowance + 
            #                  Cellphone Allowance + Data Service Allowance
            cash_component = payslip_data['payslip']['cash_allowance']
            car_allowance = payslip_data['payslip']['car_allowance'] * 0.8  # Only 80% taxable
            housing_allowance = payslip_data['payslip']['housing_allowance']
            cellphone_allowance = payslip_data['payslip']['cellphone_allowance']
            data_service_allowance = payslip_data['payslip']['data_service_allowance']
            
            taxable_income_monthly = (
                cash_component + car_allowance + housing_allowance + 
                cellphone_allowance + data_service_allowance
            )
            taxable_income_annual = taxable_income_monthly * 12
            
            # 2. Calculate Taxable Deductions (Pension EE + ER)
            # The tax deductible is BOTH pension employee AND pension employer contributions
            pension_ee_monthly = payslip_data['payslip']['pension_employee']
            pension_er_monthly = payslip_data['payslip']['pension_employer']
            total_pension_monthly = pension_ee_monthly + pension_er_monthly
            total_pension_annual = total_pension_monthly * 12
            
            # 3. Calculate Net Taxable Income (After Pension Deduction)
            taxable_income = taxable_income_annual - total_pension_annual
            
            # 4. Calculate Gross Tax using SARS 2024 brackets
            settings = load_tax_settings()
            gross_tax = calculate_tax(taxable_income, settings)
        
            # 5. Apply Primary Rebate (Age-based)
            # Get employee age if available, default to 0 if not provided
            employee_age = safe_float(employee_row.get('AGE', 0))
            
            primary_rebate = settings.get('rebate_primary', 17235)
            
            # Age-based rebates
            secondary_rebate = 0
            tertiary_rebate = 0
            if employee_age >= 75:
                tertiary_rebate = settings.get('rebate_tertiary', 3145)
                secondary_rebate = settings.get('rebate_secondary', 9444)
            elif employee_age >= 65:
                secondary_rebate = settings.get('rebate_secondary', 9444)
            
            total_rebate = primary_rebate + secondary_rebate + tertiary_rebate
            
            # 6. Apply Medical Tax Credit (MTC)
            medical_credit_annual = 0
            if payslip_data['payslip']['medical_employee'] > 0:
                main_member_count = safe_float(employee_row.get('MEDICALMAINMEMBER', 1))
                first_dependent_count = safe_float(employee_row.get('MEDICALFIRSTDEPENDENT', 0))
                additional_dependents = safe_float(employee_row.get('MEDICALADDITIONAL', 0))
                
                total_first_two = min(main_member_count + first_dependent_count, 2)
                total_additional = additional_dependents
                
                medical_credit_monthly = (total_first_two * 364) + (total_additional * 246)
                medical_credit_annual = medical_credit_monthly * 12
            
            # 7. Calculate Annual Tax
            annual_tax = gross_tax - total_rebate - medical_credit_annual
            annual_tax = max(0, annual_tax)
            
            # 8. Calculate Monthly Tax
            monthly_tax = round(annual_tax / 12, 2)
            payslip_data['payslip']['tax'] = monthly_tax
            
            # 9. Calculate Tax on Bonus
            bonus_annual = payslip_data['payslip']['bonus']
            bonus_tax_rate = 0.18
            bonus_tax_annual = bonus_annual * bonus_tax_rate
            bonus_tax_monthly_provision = round(bonus_tax_annual / 12, 2)
            payslip_data['payslip']['bonus_tax_provision'] = bonus_tax_monthly_provision
            
            # 10. Calculate Total Tax (Monthly Tax + Bonus Tax Provision)
            total_tax_monthly = monthly_tax + bonus_tax_monthly_provision
            payslip_data['payslip']['total_tax'] = round(total_tax_monthly, 2)
            
            logger.info(f"CALCULATED tax for {employee_id}: R{total_tax_monthly:.2f}")
        
        # Calculate total deductions
        total_deductions = (
            payslip_data['payslip']['pension_employee'] + 
            payslip_data['payslip']['medical_employee'] + 
            payslip_data['payslip']['group_life_employee'] + 
            payslip_data['payslip']['uif_employee'] + 
            payslip_data['payslip']['total_tax']  # Use total_tax instead of separate tax + bonus_tax_provision
        )
        payslip_data['payslip']['total_deductions'] = round(total_deductions, 2)
        
        # Calculate net pay
        payslip_data['payslip']['net_pay'] = round(payslip_data['payslip']['total_earnings'] - total_deductions, 2)
        
        # Add package breakdown information for Rand Water format
        payslip_data['payslip']['package_breakdown'] = {
            'tctc_monthly': payslip_data['payslip']['tctc'],
            'bonus_provision_monthly': round(bonus_provision_monthly, 2),
            'basic_salary_after_bonus': round(payslip_data['payslip']['tctc'] - bonus_provision_monthly, 2),
            'employer_contributions': round(total_employer_contributions, 2),
            'other_earnings': round(payslip_data['payslip']['total_earnings'] - payslip_data['payslip']['pensionable_salary'], 2),
            'pensionable_salary_breakdown': {
                'total_package': payslip_data['payslip']['tctc'],
                'housing_allowance': -payslip_data['payslip']['housing_allowance'],
                'employer_contributions': -total_employer_contributions,
                'bonus_provision': -bonus_provision_monthly,
                'car_allowance': payslip_data['payslip']['car_allowance'] if payslip_data['payslip']['car_allowance'] > 0 else 0
            }
        }
        
        # If accessed by employee (not admin), render HTML template; otherwise return JSON
        if session.get('employee_id') and not is_admin and not request.args.get('api'):
            return render_template('employee_payslip.html',
                                 employee=payslip_data['employee'],
                                 payslip=payslip_data['payslip'],
                                 config=RANDWATER_CONFIG)
        else:
            # Return JSON for admin/modal access
            return jsonify(payslip_data)
        
    except Exception as e:
        logger.error(f"Error getting employee payslip: {str(e)}")
        if session.get('employee_id'):
            return f"Error loading payslip: {str(e)}", 500
        else:
            return jsonify({'error': f'Failed to load payslip data: {str(e)}'}), 500

@app.route('/salary_simulator')
def salary_simulator():
    """Net Pay Calculator (Salary Simulator) - Real-time calculations"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        # Load tax settings for calculations
        tax_settings = load_tax_settings()
        medical_aid_rates = load_medical_aid_rates()
        
        return render_template('salary_simulator_enhanced.html', 
                             config=RANDWATER_CONFIG,
                             tax_settings=tax_settings,
                             medical_aid_rates=medical_aid_rates)
    except Exception as e:
        logger.error(f"Error loading salary simulator: {str(e)}")
        return f"Error loading salary simulator: {str(e)}", 500

@app.route('/net_pay_calculate', methods=['POST'])
def net_pay_calculate():
    """Calculate net pay for salary simulator (no CTC constraints)"""
    try:
        data = request.get_json()
        
        # Net Pay Calculator allows free input - no CTC constraints
        basic_salary = float(data.get('basic_salary', 0))
        car_allowance = float(data.get('car_allowance', 0))
        housing_allowance = float(data.get('housing_allowance', 0))
        transport_allowance = float(data.get('transport_allowance', 0))
        cellphone_allowance = float(data.get('cellphone_allowance', 0))
        data_service_allowance = float(data.get('data_service_allowance', 0))
        bonus = float(data.get('bonus', 0))
        
        # Medical aid options with subsidized/unsubsidized members
        medical_aid_provider = data.get('medical_aid_provider', 'none')
        medical_aid_option = data.get('medical_aid_option', 'none')
        subsidized_adults = int(data.get('subsidized_adults', 0))
        subsidized_children = int(data.get('subsidized_children', 0))
        unsubsidized_adults = int(data.get('unsubsidized_adults', 0))
        unsubsidized_children = int(data.get('unsubsidized_children', 0))
        
        # Retirement fund options
        retirement_fund_name = data.get('retirement_fund_name', 'RWPROV')
        retirement_fund_option = data.get('retirement_fund_option', 'option_a')
        
        # Band range affects medical aid rates
        band_range = data.get('band_range', 'o_to_q')
        
        # Calculate total gross income
        gross_monthly = (basic_salary + car_allowance + housing_allowance + 
                        transport_allowance + cellphone_allowance + data_service_allowance + bonus)
        
        # Calculate medical aid costs
        medical_aid_cost = calculate_medical_aid_cost(
            medical_aid_provider, medical_aid_option, band_range,
            subsidized_adults, subsidized_children, 
            unsubsidized_adults, unsubsidized_children
        )
        
        # Calculate pension contribution
        pension_rate = get_pension_rate(retirement_fund_name, retirement_fund_option)
        pension_contribution = basic_salary * pension_rate
        
        # Calculate tax and UIF
        tax_calculations = calculate_employee_deductions({
            'basic_salary': basic_salary,
            'car_allowance': car_allowance,
            'housing_allowance': housing_allowance,
            'transport_allowance': transport_allowance,
            'cellphone_allowance': cellphone_allowance,
            'data_service_allowance': data_service_allowance,
            'bonus': bonus,
            'medical_aid': medical_aid_cost,
            'pension_fund': pension_contribution
        })
        
        # Calculate net pay
        total_deductions = (tax_calculations['paye_tax'] + 
                          tax_calculations['uif_contribution'] + 
                          medical_aid_cost + 
                          pension_contribution)
        
        net_pay = gross_monthly - total_deductions
        
        return jsonify({
            'success': True,
            'gross_monthly': round(gross_monthly, 2),
            'paye_tax': tax_calculations['paye_tax'],
            'uif_contribution': tax_calculations['uif_contribution'],
            'medical_aid_cost': round(medical_aid_cost, 2),
            'pension_contribution': round(pension_contribution, 2),
            'total_deductions': round(total_deductions, 2),
            'net_pay': round(net_pay, 2),
            'warnings': get_validation_warnings(data, gross_monthly)
        })
        
    except Exception as e:
        logger.error(f"Error calculating net pay: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def calculate_medical_aid_cost(provider, option, band_range, sub_adults, sub_children, unsub_adults, unsub_children):
    """Calculate medical aid cost based on provider, option, and members"""
    try:
        medical_aid_rates = load_medical_aid_rates()
        
        if provider == 'none':
            return 0
        
        # Get base rates for the provider and option
        provider_rates = medical_aid_rates.get(provider, {})
        option_rates = provider_rates.get(option, {})
        
        if not option_rates:
            return 0
        
        # Band range affects rates (lower band gets 1/3 of rates)
        rate_multiplier = 1.0 if band_range == 'o_to_q' else 0.33
        
        # Calculate costs
        main_member_cost = option_rates.get('main_member', 0) * rate_multiplier
        spouse_cost = option_rates.get('spouse', 0) * rate_multiplier * sub_adults
        child_cost = option_rates.get('child', 0) * rate_multiplier * sub_children
        
        # Unsubsidized members pay full rates
        unsub_adult_cost = option_rates.get('spouse', 0) * unsub_adults
        unsub_child_cost = option_rates.get('child', 0) * unsub_children
        
        total_cost = main_member_cost + spouse_cost + child_cost + unsub_adult_cost + unsub_child_cost
        
        return total_cost
        
    except Exception as e:
        logger.error(f"Error calculating medical aid cost: {str(e)}")
        return 0

def get_pension_rate(fund_name, fund_option):
    """Get pension contribution rate based on fund and option"""
    pension_rates = {
        'RWPROV': {
            'option_a': 0.075,  # 7.5%
            'option_b': 0.10,   # 10%
            'option_d': 0.125,  # 12.5%
            'option_e': 0.15,   # 15%
            'option_f': 0.175,  # 17.5%
            'option_g': 0.20,   # 20%
        },
        'RWMPPROV': {
            'option_a': 0.06,   # 6%
            'option_b': 0.08,   # 8%
            'option_c': 0.10,   # 10%
        },
        'SAMWU': {
            'samwu': 0.075,     # 7.5%
        }
    }
    
    return pension_rates.get(fund_name, {}).get(fund_option, 0.075)

def get_validation_warnings(data, gross_monthly):
    """Generate validation warnings for net pay calculator"""
    warnings = []
    
    # Check if CTC is reasonable (this is just informational for net pay calculator)
    if gross_monthly > 100000:
        warnings.append("High CTC: Consider reviewing the package structure")
    
    # Check basic salary percentage
    basic_percentage = (float(data.get('basic_salary', 0)) / max(gross_monthly, 1)) * 100
    if basic_percentage < 50:
        warnings.append(f"Basic salary is {basic_percentage:.1f}% of total (below typical 50% minimum)")
    elif basic_percentage > 70:
        warnings.append(f"Basic salary is {basic_percentage:.1f}% of total (above typical 70% maximum)")
    
    return warnings

def load_medical_aid_rates():
    """Load medical aid rates from file"""
    try:
        with open('medical_aid_rates.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load medical aid rates: {str(e)}")
        # Return default medical aid rates
        return {
            "rand_water": {
                "option_a": {
                    "main_member": 1200.00,
                    "spouse": 1200.00,
                    "child": 400.00
                },
                "option_b": {
                    "main_member": 1500.00,
                    "spouse": 1500.00,
                    "child": 500.00
                }
            },
            "bonitas": {
                "standard": {
                    "main_member": 1400.00,
                    "spouse": 1400.00,
                    "child": 450.00
                }
            }
        }

@app.route('/api/update-employee-access', methods=['POST'])
def update_employee_access():
    """Update employee access dates"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        employee_ids = data.get('employee_ids', [])
        access_granted = data.get('access_granted')
        access_expires = data.get('access_expires')
        action = data.get('action', 'update')
        
        print(f"=== BULK UPDATE DEBUG START ===")
        print(f"Employee IDs: {employee_ids}")
        print(f"Access Granted: {access_granted}")
        print(f"Access Expires: {access_expires}")
        print(f"Action: {action}")
        
        if not employee_ids:
            return jsonify({'error': 'No employees selected'}), 400
        
        if not access_granted or not access_expires:
            return jsonify({'error': 'Access dates are required'}), 400
        
        # Load current employee access data
        try:
            with open('employee_access.json', 'r') as f:
                employee_access = json.load(f)
            print(f"Loaded {len(employee_access)} employee access records")
        except Exception as e:
            print(f"Error loading employee access: {e}")
            employee_access = []
        
        updated_count = 0
        
        # Update access dates for selected employees
        for emp_access in employee_access:
            if emp_access['employee_id'] in employee_ids:
                print(f"Updating employee {emp_access['employee_id']}: {emp_access['access_granted']} -> {access_granted}, {emp_access['access_expires']} -> {access_expires}")
                emp_access['access_granted'] = access_granted
                emp_access['access_expires'] = access_expires
                emp_access['status'] = 'ACTIVE'
                updated_count += 1
        
        print(f"Updated {updated_count} employees")
        
        # Save updated data
        with open('employee_access.json', 'w') as f:
            json.dump(employee_access, f, indent=2)
        
        print(f"Saved updated data to employee_access.json")
        print(f"=== BULK UPDATE DEBUG END ===")
        
        # Log the update operation
        current_user = session.get('username', 'Unknown User')
        save_system_log({
            'action': 'UPDATE_ACCESS_DATES',
            'user': current_user,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'details': {
                'action_type': action,
                'updated_count': updated_count,
                'employee_ids': employee_ids,
                'access_granted': access_granted,
                'access_expires': access_expires
            }
        })
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated access dates for {updated_count} employees',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        print(f"=== BULK UPDATE ERROR ===")
        print(f"Error: {str(e)}")
        print(f"=== BULK UPDATE ERROR END ===")
        logger.error(f"Update employee access failed: {e}")
        return jsonify({'error': 'Failed to update access dates', 'details': str(e)}), 500

@app.route('/api/revoke-employee-access', methods=['POST'])
def revoke_employee_access():
    """Revoke employee access"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        employee_ids = data.get('employee_ids', [])
        action = data.get('action', 'revoke')
        
        if not employee_ids:
            return jsonify({'error': 'No employees selected'}), 400
        
        # Load current employee access data
        try:
            with open('employee_access.json', 'r') as f:
                employee_access = json.load(f)
        except:
            employee_access = []
        
        revoked_count = 0
        
        # Revoke access for selected employees
        for emp_access in employee_access:
            if emp_access['employee_id'] in employee_ids:
                emp_access['status'] = 'REVOKED'
                revoked_count += 1
        
        # Save updated data
        with open('employee_access.json', 'w') as f:
            json.dump(employee_access, f, indent=2)
        
        # Log the revoke operation
        current_user = session.get('username', 'Unknown User')
        save_system_log({
            'action': 'REVOKE_ACCESS',
            'user': current_user,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'details': {
                'action_type': action,
                'revoked_count': revoked_count,
                'employee_ids': employee_ids
            }
        })
        
        return jsonify({
            'success': True,
            'message': f'Successfully revoked access for {revoked_count} employees',
            'revoked_count': revoked_count
        }), 200
        
    except Exception as e:
        logger.error(f"Revoke employee access failed: {e}")
        return jsonify({'error': 'Failed to revoke access', 'details': str(e)}), 500

@app.route('/api/restore-employee-access', methods=['POST'])
def restore_employee_access():
    """Restore employee access"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        employee_ids = data.get('employee_ids', [])
        
        if not employee_ids:
            return jsonify({'error': 'No employees selected'}), 400
        
        # Load current employee access data
        try:
            with open('employee_access.json', 'r') as f:
                employee_access = json.load(f)
        except:
            employee_access = []
        
        restored_count = 0
        
        # Restore access for selected employees
        for emp_access in employee_access:
            if emp_access['employee_id'] in employee_ids:
                emp_access['status'] = 'ACTIVE'
                # Set new access dates (30 days from now)
                from datetime import datetime, timedelta
                emp_access['access_granted'] = datetime.now().strftime('%Y-%m-%d')
                emp_access['access_expires'] = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                restored_count += 1
        
        # Save updated data
        with open('employee_access.json', 'w') as f:
            json.dump(employee_access, f, indent=2)
        
        # Log the restore operation
        current_user = session.get('username', 'Unknown User')
        save_system_log({
            'action': 'RESTORE_ACCESS',
            'user': current_user,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'details': {
                'restored_count': restored_count,
                'employee_ids': employee_ids
            }
        })
        
        return jsonify({
            'success': True,
            'message': f'Successfully restored access for {restored_count} employees',
            'restored_count': restored_count
        }), 200
        
    except Exception as e:
        logger.error(f"Restore employee access failed: {e}")
        return jsonify({'error': 'Failed to restore access', 'details': str(e)}), 500

@app.route('/api/package-details/<employee_id>')
def get_package_details_api(employee_id):
    """API endpoint to get package details for admin view"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        print(f"\n=== PACKAGE DETAILS API DEBUG START ===")
        print(f"Requested employee ID: {employee_id}")
        
        # Get employee data
        active_employees = get_active_randwater_employees()
        print(f"Total active employees found: {len(active_employees)}")
        
        employee = None
        for emp in active_employees:
            print(f"Checking employee: {emp['employee_id']} vs {employee_id}")
            if emp['employee_id'] == employee_id:
                employee = emp
                print(f"✓ Found matching employee: {employee_id}")
                break
        
        if not employee:
            print(f"❌ Employee {employee_id} not found!")
            return jsonify({'error': 'Employee not found'}), 404
        
        print(f"Employee data keys: {list(employee.keys())}")
        print(f"Basic salary: {employee.get('basic_salary', 'NOT_FOUND')}")
        print(f"Housing allowance: {employee.get('housing_allowance', 'NOT_FOUND')}")
        print(f"Car allowance: {employee.get('car_allowance', 'NOT_FOUND')}")
        print(f"Pension fund: {employee.get('pension_fund', 'NOT_FOUND')}")
        print(f"Medical aid: {employee.get('medical_aid', 'NOT_FOUND')}")
        print(f"CTC: {employee.get('ctc', 'NOT_FOUND')}")
        
        # Get audit trail for this package
        audit_trail = get_package_audit_trail(employee_id)
        print(f"Audit trail entries: {len(audit_trail)}")
        
        # Get notifications for this employee
        notifications = get_employee_notifications(employee_id)
        print(f"Notifications: {len(notifications)}")
        
        # Format data for the frontend
        package_data = {
            'employee_id': employee['employee_id'],
            'employee_name': f"{employee.get('first_name', '')} {employee.get('surname', '')}".strip(),
            'grade_band': employee.get('grade_band', ''),
            'department': employee.get('department', ''),
            'job_title': employee.get('job_title', ''),
            'sap_data': {
                'basic_salary': employee.get('basic_salary', 0),
                'car_allowance': employee.get('car_allowance', 0),
                'housing_allowance': employee.get('housing_allowance', 0),
                'cellphone_allowance': employee.get('cellphone_allowance', 0),
                'data_service_allowance': employee.get('data_service_allowance', 0),
                'pension_fund': employee.get('pension_fund', 0),
                'medical_aid': employee.get('medical_aid', 0),
                'bonus': employee.get('bonus', 0),
                'critical_skills': employee.get('critical_skills', 0),
                'ctc': employee.get('ctc', 0)
            },
            'package_components': {
                'basic_salary': employee.get('basic_salary', 0),
                'car_allowance': employee.get('car_allowance', 0),
                'housing_allowance': employee.get('housing_allowance', 0),
                'cellphone_allowance': employee.get('cellphone_allowance', 0),
                'data_service_allowance': employee.get('data_service_allowance', 0),
                'pension_fund': employee.get('pension_fund', 0),
                'medical_aid': employee.get('medical_aid', 0),
                'bonus': employee.get('bonus', 0),
                'critical_skills': employee.get('critical_skills', 0),
                'tctc': employee.get('ctc', 0)
            },
            'access_granted': employee.get('access_granted', ''),
            'access_expires': employee.get('access_expires', ''),
            'access_status': employee.get('access_status', 'ACTIVE'),
            'package_submitted': employee.get('package_submitted', False)
        }
        
        print(f"Formatted package data:")
        print(f"  SAP data: {package_data['sap_data']}")
        print(f"  Package components: {package_data['package_components']}")
        print(f"=== PACKAGE DETAILS API DEBUG END ===\n")
        
        return jsonify({
            'success': True,
            'package': package_data,
            'audit_trail': audit_trail,
            'notifications': notifications
        }), 200
        
    except Exception as e:
        print(f"❌ ERROR in package details API: {str(e)}")
        logger.error(f"Error getting package details for {employee_id}: {str(e)}")
        return jsonify({'error': 'Failed to load package details', 'details': str(e)}), 500

@app.route('/api/admin/package/<employee_id>')
def get_package_for_admin(employee_id):
    """Get package data for admin viewing in manage_packages modal"""
    # Allow both admins and employees (employees can only access their own data)
    is_admin = session.get('admin') or session.get('isRandWaterAdmin')
    is_employee = session.get('employee_id') == employee_id
    
    if not is_admin and not is_employee:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get employee data from active employees
        active_employees = get_active_randwater_employees()
        employee = None
        for emp in active_employees:
            if emp['employee_id'] == employee_id:
                employee = emp
                break
        
        if not employee:
            return jsonify({'success': False, 'error': 'Package not found'}), 404
        
        # Format data for the frontend (same structure as get_package_details_api)
        package_data = {
                'employee_id': employee['employee_id'],
                'employee_name': f"{employee.get('first_name', '')} {employee.get('surname', '')}".strip(),
                'grade_band': employee.get('grade_band', ''),
                'department': employee.get('department', ''),
                'job_title': employee.get('job_title', ''),
                'sap_data': {
                    'basic_salary': employee.get('basic_salary', 0),
                    'car_allowance': employee.get('car_allowance', 0),
                    'housing_allowance': employee.get('housing_allowance', 0),
                    'cellphone_allowance': employee.get('cellphone_allowance', 0),
                    'data_service_allowance': employee.get('data_service_allowance', 0),
                    'pension_fund': employee.get('pension_fund', 0),
                    'medical_aid': employee.get('medical_aid', 0),
                    'bonus': employee.get('bonus', 0),
                    'ctc': employee.get('ctc', 0),
                    'TPE': employee.get('basic_salary', 0),
                    'PENSION_FUND': employee.get('pension_fund', 0),
                    'PENSIONOPTION': employee.get('pension_option', 'B'),
                    'MEDICAL': employee.get('medical_provider', 'N/A'),
                    'MEDICALOPTION': employee.get('medical_option', 'N/A'),
                    'MEDICALEECONTRIBUTION': employee.get('medical_er_contribution', 0),
                    'CELLPHONEALLOWANCE': employee.get('cellphone_allowance', 0),
                    'DATASERVICEALLOWANCE': employee.get('data_service_allowance', 0),
                    'HOUSING': employee.get('housing_allowance', 0)
                },
                'package_components': {
                    'basic_salary': employee.get('basic_salary', 0),
                    'car_allowance': employee.get('car_allowance', 0),
                    'housing_allowance': employee.get('housing_allowance', 0),
                    'cellphone_allowance': employee.get('cellphone_allowance', 0),
                    'data_service_allowance': employee.get('data_service_allowance', 0),
                    'pension_fund': employee.get('pension_fund', 0),
                    'medical_aid': employee.get('medical_aid', 0),
                    'bonus': employee.get('bonus', 0),
                    'employee_subgroup': employee.get('employee_subgroup', 'other'),
                    'band_range': employee.get('band_range', 'o_to_q'),
                    'pension_option': employee.get('pension_option', 'B'),
                    'group_life_option': employee.get('group_life_option', 'standard'),
                    'bonus_type': employee.get('bonus_type', 'monthly'),
                    'tctc': employee.get('ctc', 0),
                    'pension_ee': employee.get('pension_ee', 0),
                    'pension_er': employee.get('pension_er', 0),
                    'group_life_ee': employee.get('group_life_ee', 0),
                    'group_life_er': employee.get('group_life_er', 0),
                    'cash_component': employee.get('cash_component', 0)
                },
                'current_tctc': employee.get('ctc', 0),
                'tctc_limit': employee.get('ctc', 0),
                'access_granted': employee.get('access_granted', ''),
                'access_expires': employee.get('access_expires', ''),
                'access_status': 'EXPIRED' if employee.get('is_expired', False) else 'ACTIVE',
                'package_submitted': employee.get('package_submitted', False)
            }
        
        return jsonify({
            'success': True,
            'package': package_data
        })
        
    except Exception as e:
        logger.error(f"Error getting package for {employee_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/package/<employee_id>/save-draft', methods=['POST'])
def save_package_draft(employee_id):
    """Save package as draft"""
    # Allow both admins and employees (employees can only save their own data)
    is_admin = session.get('admin') or session.get('isRandWaterAdmin')
    is_employee = session.get('employee_id') == employee_id
    
    if not is_admin and not is_employee:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        package_components = data.get('package_components', {})
        
        # Save to drafts folder
        draft_file = f'drafts/package_{employee_id}.json'
        os.makedirs('drafts', exist_ok=True)
        
        saved_by = session.get('username', 'Unknown User')
        if is_employee:
            saved_by = f"Employee {employee_id}"
        
        draft_data = {
            'employee_id': employee_id,
            'package_components': package_components,
            'status': 'draft',
            'saved_by': saved_by,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(draft_file, 'w') as f:
            json.dump(draft_data, f, indent=2)
        
        # If admin saved the draft, create audit entry and notification
        if is_admin:
            # Create audit trail entry
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'DRAFT_SAVED',
                'admin_user': saved_by,
                'changes': 'Package draft saved by admin',
                'details': f"TPE: R{package_components.get('tpe', 0)}, Car: R{package_components.get('car_allowance', 0)}"
            }
            
            # Load and update audit trail
            audit_file = 'randwater_package_audit.json'
            if os.path.exists(audit_file):
                with open(audit_file, 'r') as f:
                    all_audits = json.load(f)
            else:
                all_audits = {}
            
            if employee_id not in all_audits:
                all_audits[employee_id] = []
            all_audits[employee_id].append(audit_entry)
            
            with open(audit_file, 'w') as f:
                json.dump(all_audits, f, indent=2)
            
            # Create employee notification
            create_employee_notification(
                employee_id,
                f"Admin ({saved_by}) modified your compensation package draft. Please review the changes.",
                saved_by
            )
        
        logger.info(f"Draft saved for {employee_id} by {saved_by}")
        return jsonify({'success': True, 'message': 'Draft saved successfully'})
        
    except Exception as e:
        logger.error(f"Error saving draft for {employee_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/package/<employee_id>/load-draft')
def load_package_draft(employee_id):
    """Load saved draft for a package"""
    # Allow both admins and employees (employees can only load their own data)
    is_admin = session.get('admin') or session.get('isRandWaterAdmin')
    is_employee = session.get('employee_id') == employee_id
    
    if not is_admin and not is_employee:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        draft_file = f'drafts/package_{employee_id}.json'
        
        if os.path.exists(draft_file):
            with open(draft_file, 'r') as f:
                draft_data = json.load(f)
            logger.info(f"Draft loaded for {employee_id}")
            return jsonify({'success': True, 'draft': draft_data})
        else:
            return jsonify({'success': False, 'message': 'No draft found'})
        
    except Exception as e:
        logger.error(f"Error loading draft for {employee_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/package/<employee_id>/submit', methods=['POST'])
def submit_package_final(employee_id):
    """Submit package as final for SAP export"""
    # Allow both admins and employees (employees can only submit their own data)
    is_admin = session.get('admin') or session.get('isRandWaterAdmin')
    is_employee = session.get('employee_id') == employee_id
    
    if not is_admin and not is_employee:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        package_components = data.get('package_components', {})
        
        # Get employee data
        active_employees = get_active_randwater_employees()
        employee = next((e for e in active_employees if e['employee_id'] == employee_id), None)
        
        if not employee:
            return jsonify({'success': False, 'error': 'Employee not found'}), 404
        
        # Save to submitted packages
        submitted_file = 'submitted_packages.json'
        if os.path.exists(submitted_file):
            with open(submitted_file, 'r') as f:
                submitted = json.load(f)
        else:
            submitted = []
        
        # Check if already submitted
        existing = next((p for p in submitted if p['employee_id'] == employee_id), None)
        
        submitted_package = {
            'employee_id': employee_id,
            'employee_name': f"{employee.get('first_name', '')} {employee.get('surname', '')}".strip(),
            'package_components': package_components,
            'status': 'submitted',
            'submitted_by': session.get('username', 'admin'),
            'submitted_at': datetime.now().isoformat(),
            'grade_band': employee.get('grade_band'),
            'department': employee.get('department')
        }
        
        if existing:
            # Update existing
            submitted = [p for p in submitted if p['employee_id'] != employee_id]
        
        submitted.append(submitted_package)
        
        with open(submitted_file, 'w') as f:
            json.dump(submitted, f, indent=2)
        
        logger.info(f"Package submitted for {employee_id}")
        return jsonify({'success': True, 'message': 'Package submitted successfully'})
        
    except Exception as e:
        logger.error(f"Error submitting package for {employee_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/debug-employee-data')
def debug_employee_data():
    """Debug endpoint to check employee data loading"""
    try:
        print(f"\n=== DEBUG EMPLOYEE DATA START ===")
        
        # Check if employee_access.json exists
        employee_access_exists = os.path.exists('employee_access.json')
        print(f"employee_access.json exists: {employee_access_exists}")
        
        if employee_access_exists:
            with open('employee_access.json', 'r') as f:
                employee_access = json.load(f)
            print(f"Employee access records: {len(employee_access)}")
            for emp in employee_access:
                print(f"  - {emp['employee_id']}: {emp['first_name']} {emp['surname']}")
        else:
            print("No employee access file found")
        
        # Check SAP uploads
        sap_uploads = load_sap_uploads()
        print(f"SAP uploads found: {len(sap_uploads) if sap_uploads else 0}")
        
        if sap_uploads:
            latest_upload = max(sap_uploads, key=lambda x: x['upload_date'])
            print(f"Latest upload: {latest_upload.get('filename')}")
            print(f"Employee data count: {len(latest_upload.get('employee_data', []))}")
            
            # Show first employee's data
            if latest_upload.get('employee_data'):
                first_emp = latest_upload['employee_data'][0]
                print(f"First employee data:")
                print(f"  EMPLOYEECODE: {first_emp.get('EMPLOYEECODE')}")
                print(f"  TPE: {first_emp.get('TPE')}")
                print(f"  HOUSING: {first_emp.get('HOUSING')}")
                print(f"  PENSIONEECONTRIBUTION: {first_emp.get('PENSIONEECONTRIBUTION')}")
                print(f"  MEDICALEECONTRIBUTION: {first_emp.get('MEDICALEECONTRIBUTION')}")
                print(f"  BONUSPROVISION: {first_emp.get('BONUSPROVISION')}")
        
        # Check completed packages
        completed_packages = get_all_randwater_completed_packages()
        print(f"Completed packages: {len(completed_packages)}")
        
        print(f"=== DEBUG EMPLOYEE DATA END ===\n")
        
        return jsonify({
            'success': True,
            'employee_access_exists': employee_access_exists,
            'employee_access_count': len(employee_access) if employee_access_exists else 0,
            'sap_uploads_count': len(sap_uploads) if sap_uploads else 0,
            'completed_packages_count': len(completed_packages)
        })
        
    except Exception as e:
        print(f"Debug error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-sap-data')
def test_sap_data():
    """Test endpoint to check SAP data loading"""
    try:
        sap_uploads = load_sap_uploads()
        if sap_uploads:
            latest_upload = max(sap_uploads, key=lambda x: x['upload_date'])
            sap_data = {emp['EMPLOYEECODE']: emp for emp in latest_upload.get('employee_data', [])}
            return jsonify({
                'success': True,
                'sap_uploads_count': len(sap_uploads),
                'latest_upload': latest_upload.get('filename'),
                'employee_count': len(latest_upload.get('employee_data', [])),
                'employee_codes': list(sap_data.keys()),
                'rw001_data': sap_data.get('RW001', {}),
                'rw001_tpe': sap_data.get('RW001', {}).get('TPE', 'Not found'),
                'rw001_tctc': sap_data.get('RW001', {}).get('TCTC', 'Not found')
            }), 200
        else:
            return jsonify({'success': False, 'error': 'No SAP uploads found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/package_edit_fullpage/<employee_id>')
def package_edit_fullpage(employee_id):
    """Admin full-page package edit interface"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        # Get employee data
        active_employees = get_active_randwater_employees()
        employee = None
        for emp in active_employees:
            if emp['employee_id'] == employee_id:
                employee = emp
                break
        
        if not employee:
            return redirect(url_for('manage_packages'))
        
        # Check if package has been submitted - if so, redirect to manage_packages with a message
        if employee.get('package_submitted', False):
            flash('This package has already been submitted and cannot be edited.', 'warning')
            return redirect(url_for('manage_packages'))
        
        # Get audit trail for this package
        audit_trail = get_package_audit_trail(employee_id)
        
        # Admin view - no notifications (notifications are for employee login only)
        notifications = []
        
        return render_template('package_edit_fullpage.html', 
                             config=RANDWATER_CONFIG,
                             employee=employee,
                             audit_trail=audit_trail,
                             notifications=notifications)
        
    except Exception as e:
        logger.error(f"Error loading fullpage edit for {employee_id}: {str(e)}")
        return redirect(url_for('manage_packages'))

@app.route('/api/password-policy', methods=['GET'])
def get_password_policy():
    """Get current password policy settings"""
    if not session.get('admin') and not session.get('isRandWaterAdmin') and not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        policy = load_password_policy()
        return jsonify({
            'success': True,
            'policy': policy
        }), 200
    except Exception as e:
        logger.error(f"Get password policy failed: {e}")
        return jsonify({'error': 'Failed to load password policy', 'details': str(e)}), 500

@app.route('/api/password-policy', methods=['POST'])
def update_password_policy():
    """Update password policy settings"""
    if not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized - Super Admin access required'}), 401
    
    try:
        data = request.get_json()
        new_policy = data.get('policy', {})
        
        # Validate policy settings
        if 'min_length' in new_policy and (new_policy['min_length'] < 6 or new_policy['min_length'] > 20):
            return jsonify({'error': 'Minimum length must be between 6 and 20'}), 400
        
        if 'max_age_days' in new_policy and (new_policy['max_age_days'] < 30 or new_policy['max_age_days'] > 365):
            return jsonify({'error': 'Password expiry must be between 30 and 365 days'}), 400
        
        if 'password_history' in new_policy and (new_policy['password_history'] < 0 or new_policy['password_history'] > 10):
            return jsonify({'error': 'Password history must be between 0 and 10'}), 400
        
        # Save policy to system backup
        try:
            backup_files = [f for f in os.listdir('.') if f.startswith('backups/system_backup_') and f.endswith('.json')]
            if backup_files:
                latest_backup = max(backup_files)
                with open(latest_backup, 'r') as f:
                    backup_data = json.load(f)
                
                if 'security_settings' not in backup_data:
                    backup_data['security_settings'] = {}
                
                backup_data['security_settings']['password_policy'] = new_policy
                
                with open(latest_backup, 'w') as f:
                    json.dump(backup_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving password policy: {e}")
            return jsonify({'error': 'Failed to save password policy'}), 500
        
        # Log the policy update
        current_user = session.get('username', 'Unknown User')
        save_system_log({
            'action': 'UPDATE_PASSWORD_POLICY',
            'user': current_user,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'details': {
                'new_policy': new_policy
            }
        })
        
        return jsonify({
            'success': True,
            'message': 'Password policy updated successfully',
            'policy': new_policy
        }), 200
        
    except Exception as e:
        logger.error(f"Update password policy failed: {e}")
        return jsonify({'error': 'Failed to update password policy', 'details': str(e)}), 500

@app.route('/api/validate-password', methods=['POST'])
def validate_password_api():
    """Validate password against current policy (for frontend validation)"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        is_valid, errors = validate_password_strength(password)
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'errors': errors
        }), 200
        
    except Exception as e:
        logger.error(f"Password validation failed: {e}")
        return jsonify({'error': 'Failed to validate password', 'details': str(e)}), 500

@app.route('/admin/randwater/generate-tax-report', methods=['POST'])
def generate_tax_report():
    """Generate a detailed PDF tax calculation report"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from io import BytesIO
        from datetime import datetime
        
        data = request.json
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, 
                               topMargin=2*cm, bottomMargin=2*cm)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#003366'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#003366'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Header with logos
        from reportlab.platypus import Image
        
        # Create header table with logos
        header_data = []
        cell_data = []
        
        # Left: Rand Water logo
        logo_debug_info = []
        
        # Try different path variations
        base_dir = os.path.dirname(os.path.abspath(__file__))
        randwater_logo_path = os.path.join(base_dir, 'static', 'images', 'randwater-logo.png')
        logo_debug_info.append(f"Looking for Rand Water logo at: {randwater_logo_path}, exists: {os.path.exists(randwater_logo_path)}")
        
        if os.path.exists(randwater_logo_path):
            try:
                randwater_logo = Image(randwater_logo_path, width=6*cm, height=2*cm)
                cell_data.append(randwater_logo)
                logo_debug_info.append("Rand Water logo loaded successfully")
            except Exception as e:
                logo_debug_info.append(f"Error loading Rand Water logo: {e}")
                cell_data.append(Paragraph('<b>Rand Water</b>', styles['Normal']))
        else:
            logo_debug_info.append(f"Rand Water logo not found at: {randwater_logo_path}")
            # Add placeholder text instead of empty cell
            cell_data.append(Paragraph('<b>Rand Water</b>', styles['Normal']))
        
        # Middle: Title and info
        title_text = f"<para align='center'><b>TAX CALCULATION REPORT</b><br/><br/>Generated: {datetime.now().strftime('%d %B %Y %H:%M')}</para>"
        cell_data.append(Paragraph(title_text, styles['Normal']))
        
        # Right: GoSmartHR logo
        smartHR_logo_path = os.path.join(base_dir, 'static', 'images', 'gosmarthr-logo.png')
        logo_debug_info.append(f"Looking for SmartHR logo at: {smartHR_logo_path}, exists: {os.path.exists(smartHR_logo_path)}")
        
        if os.path.exists(smartHR_logo_path):
            try:
                smartHR_logo = Image(smartHR_logo_path, width=6*cm, height=2*cm)
                cell_data.append(smartHR_logo)
                logo_debug_info.append("SmartHR logo loaded successfully")
            except Exception as e:
                logo_debug_info.append(f"Error loading SmartHR logo: {e}")
                # Add placeholder text instead of empty cell
                cell_data.append(Paragraph('<b>GoSmartHR</b>', styles['Normal']))
        else:
            logo_debug_info.append(f"SmartHR logo not found at: {smartHR_logo_path}")
            # Add placeholder text instead of empty cell
            cell_data.append(Paragraph('<b>GoSmartHR</b>', styles['Normal']))
        
        header_data.append(cell_data)
        
        # Create header table
        header_table = Table(header_data, colWidths=[6*cm, 7*cm, 6*cm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 20))
        
        # Employee Information
        elements.append(Paragraph("Employee Information", heading_style))
        emp_data = [
            ['Employee ID:', data.get('employee_id', 'N/A')],
            ['Employee Name:', data.get('employee_name', 'N/A')],
            ['CTC:', f"R {data.get('ctc', 0):,.2f}"]
        ]
        emp_table = Table(emp_data, colWidths=[5*cm, 10*cm])
        emp_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#003366')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(emp_table)
        elements.append(Spacer(1, 20))
        
        # Step 1: Taxable Income Calculation
        elements.append(Paragraph("STEP 1: TAXABLE INCOME CALCULATION", heading_style))
        cash = data.get('cash_component', 0)
        car_full = data.get('car_allowance', 0)
        car_taxable = car_full * 0.8
        housing = data.get('housing_allowance', 0)
        cellphone = data.get('cellphone_allowance', 0)
        data_service = data.get('data_service_allowance', 0)
        
        taxable_monthly = cash + car_taxable + housing + cellphone + data_service
        taxable_annual = taxable_monthly * 12
        
        income_data = [
            ['Component', 'Monthly (R)', 'Taxable %', 'Taxable Amount (R)'],
            ['Cash Component', f'{cash:,.2f}', '100%', f'{cash:,.2f}'],
            ['Car Allowance', f'{car_full:,.2f}', '80%', f'{car_taxable:,.2f}'],
            ['Housing Allowance', f'{housing:,.2f}', '100%', f'{housing:,.2f}'],
            ['Cellphone Allowance', f'{cellphone:,.2f}', '100%', f'{cellphone:,.2f}'],
            ['Data Service Allowance', f'{data_service:,.2f}', '100%', f'{data_service:,.2f}'],
            ['TOTAL MONTHLY', '', '', f'{taxable_monthly:,.2f}'],
            ['TOTAL ANNUAL', '', '', f'{taxable_annual:,.2f}']
        ]
        
        income_table = Table(income_data, colWidths=[5*cm, 3*cm, 2.5*cm, 3.5*cm])
        income_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor('#E6F2FF')),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(income_table)
        elements.append(Spacer(1, 20))
        
        # Step 2: Pension Deductions
        elements.append(Paragraph("STEP 2: PENSION DEDUCTIONS (TAX DEDUCTIBLE)", heading_style))
        pension_ee = data.get('pension_ee', 0)
        pension_er = data.get('pension_er', 0)
        total_pension_monthly = pension_ee + pension_er
        total_pension_annual = total_pension_monthly * 12
        
        pension_data = [
            ['Component', 'Monthly (R)', 'Annual (R)'],
            ['Pension Employee Contribution', f'{pension_ee:,.2f}', f'{pension_ee * 12:,.2f}'],
            ['Pension Employer Contribution', f'{pension_er:,.2f}', f'{pension_er * 12:,.2f}'],
            ['TOTAL PENSION DEDUCTION', f'{total_pension_monthly:,.2f}', f'{total_pension_annual:,.2f}']
        ]
        
        pension_table = Table(pension_data, colWidths=[7*cm, 3.5*cm, 3.5*cm])
        pension_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E6F2FF')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(pension_table)
        elements.append(Spacer(1, 20))
        
        # Step 3: Net Taxable Income
        elements.append(Paragraph("STEP 3: NET TAXABLE INCOME", heading_style))
        net_taxable = taxable_annual - total_pension_annual
        
        net_data = [
            ['Description', 'Amount (R)'],
            ['Taxable Income (Annual)', f'{taxable_annual:,.2f}'],
            ['Less: Pension Deduction (EE + ER)', f'({total_pension_annual:,.2f})'],
            ['NET TAXABLE INCOME', f'{net_taxable:,.2f}']
        ]
        
        net_table = Table(net_data, colWidths=[10*cm, 4*cm])
        net_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFE6E6')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(net_table)
        elements.append(Spacer(1, 20))
        
        # Page Break
        elements.append(PageBreak())
        
        # SARS Tax Tables
        elements.append(Paragraph("SOUTH AFRICAN REVENUE SERVICE (SARS)", heading_style))
        elements.append(Paragraph("Tax Brackets 2024/2025 Tax Year", heading_style))
        
        sars_data = [
            ['Taxable Income (R)', 'Rates of Tax (R)'],
            ['1 – 237 100', '18% of taxable income'],
            ['237 101 – 370 500', '42 678 + 26% of taxable income above 237 100'],
            ['370 501 – 512 800', '77 362 + 31% of taxable income above 370 500'],
            ['512 801 – 673 000', '121 475 + 36% of taxable income above 512 800'],
            ['673 001 – 857 900', '179 147 + 39% of taxable income above 673 000'],
            ['857 901 – 1 817 000', '251 258 + 41% of taxable income above 857 900'],
            ['1 817 001 and above', '644 489 + 45% of taxable income above 1 817 000']
        ]
        
        sars_table = Table(sars_data, colWidths=[5*cm, 9*cm])
        sars_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')])
        ]))
        elements.append(sars_table)
        elements.append(Spacer(1, 20))
        
        # Step 4: Tax Calculation
        elements.append(Paragraph("STEP 4: TAX CALCULATION", heading_style))
        
        # Calculate which bracket applies
        gross_tax = 0
        bracket_info = ""
        if net_taxable <= 237100:
            gross_tax = net_taxable * 0.18
            bracket_info = "18% bracket"
        elif net_taxable <= 370500:
            gross_tax = 42678 + (net_taxable - 237100) * 0.26
            bracket_info = "26% bracket"
        elif net_taxable <= 512800:
            gross_tax = 77362 + (net_taxable - 370500) * 0.31
            bracket_info = "31% bracket"
        elif net_taxable <= 673000:
            gross_tax = 121475 + (net_taxable - 512800) * 0.36
            bracket_info = "36% bracket"
        elif net_taxable <= 857900:
            gross_tax = 179147 + (net_taxable - 673000) * 0.39
            bracket_info = "39% bracket"
        elif net_taxable <= 1817000:
            gross_tax = 251258 + (net_taxable - 857900) * 0.41
            bracket_info = "41% bracket"
        else:
            gross_tax = 644489 + (net_taxable - 1817000) * 0.45
            bracket_info = "45% bracket"
        
        # Rebates and Credits
        primary_rebate = 17235
        medical_dependents = data.get('medical_dependents', 4)
        first_two = min(medical_dependents, 2)
        additional = max(0, medical_dependents - 2)
        medical_credit_monthly = (first_two * 364) + (additional * 246)
        medical_credit_annual = medical_credit_monthly * 12
        
        annual_bonus = data.get('annual_bonus', 0)
        bonus_tax_annual = annual_bonus * 0.18
        
        annual_tax = gross_tax - primary_rebate - medical_credit_annual
        annual_tax = max(0, annual_tax)
        monthly_tax = annual_tax / 12
        bonus_tax_monthly = bonus_tax_annual / 12
        total_tax_monthly = monthly_tax + bonus_tax_monthly
        
        tax_calc_data = [
            ['Description', 'Amount (R)'],
            ['Gross Tax (SARS Brackets)', f'{gross_tax:,.2f}'],
            [f'Applicable Bracket: {bracket_info}', ''],
            ['Less: Primary Rebate', f'({primary_rebate:,.2f})'],
            [f'Less: Medical Tax Credit ({medical_dependents} dependents)', f'({medical_credit_annual:,.2f})'],
            ['ANNUAL TAX (Salary)', f'{annual_tax:,.2f}'],
            ['MONTHLY TAX (Salary)', f'{monthly_tax:,.2f}'],
            ['', ''],
            ['Bonus Tax (18% on annual bonus)', f'{bonus_tax_annual:,.2f}'],
            ['Bonus Tax (Monthly Provision)', f'{bonus_tax_monthly:,.2f}'],
            ['', ''],
            ['TOTAL MONTHLY TAX', f'{total_tax_monthly:,.2f}']
        ]
        
        tax_calc_table = Table(tax_calc_data, colWidths=[10*cm, 4*cm])
        tax_calc_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 2), (0, 2), 'Helvetica-Oblique'),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.grey),
            ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#E6F2FF')),
            ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFE6E6')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(tax_calc_table)
        
        # Footer
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("This report is generated based on SARS 2024/2025 tax year regulations.", styles['Normal']))
        elements.append(Paragraph("For official tax calculations, please consult with SARS or a qualified tax practitioner.", styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        
        # Return PDF
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Tax_Calculation_Report_{data.get('employee_id', 'Unknown')}.pdf"
        )
        
    except ImportError as e:
        logger.error(f"reportlab not installed: {e}")
        return jsonify({'error': 'PDF generation library not installed. Please contact administrator.'}), 500
    except Exception as e:
        logger.error(f"Error generating tax report: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 