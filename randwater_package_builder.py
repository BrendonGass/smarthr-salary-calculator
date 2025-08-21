from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, g, flash, make_response
import json
import math
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import requests
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import csv
from werkzeug.utils import secure_filename

# Import our models
from models import (PackageManager, EmployeeAccess, NotificationManager, 
                    email_logger, smtp_config)

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

# Initialize managers
employee_access = EmployeeAccess()
package_manager = PackageManager()
notification_manager = NotificationManager()

# Custom Jinja2 filters
@app.template_filter('strptime')
def strptime_filter(date_string, format_string):
    """Convert string to datetime object"""
    try:
        return datetime.strptime(date_string, format_string)
    except:
        return None

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

def safe_float_conversion(value, default=0.0):
    """Safely convert value to float, returning default if conversion fails"""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

# ============================================================================
# EMPLOYEE PORTAL ROUTES (Package Builder)
# ============================================================================

@app.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    """Employee login for Package Builder"""
    if session.get('employee_id'):
        return redirect(url_for('employee_package_builder'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate employee access
        access = employee_access.validate_employee_access(username, password)
        if access:
            session['employee_id'] = access['employee_id']
            session['grade_band'] = access['grade_band']
            session['username'] = access['username']
            return redirect(url_for('employee_package_builder'))
        else:
            error = "Invalid credentials or access expired"
    
    return render_template('employee_login.html', error=error, config=RANDWATER_CONFIG)

@app.route('/employee/logout')
def employee_logout():
    """Employee logout"""
    session.clear()
    return redirect(url_for('employee_login'))

@app.route('/employee/package-builder')
def employee_package_builder():
    """Main Package Builder interface for employees"""
    if not session.get('employee_id'):
        return redirect(url_for('employee_login'))
    
    # Get employee's package
    package = package_manager.get_employee_package(session['employee_id'])
    if not package:
        flash('No package found for your employee ID. Please contact HR.', 'error')
        return redirect(url_for('employee_login'))
    
    # Get notifications
    notifications = notification_manager.get_employee_notifications(session['employee_id'])
    
    return render_template('employee_package_builder.html', 
                         package=package, 
                         notifications=notifications,
                         config=RANDWATER_CONFIG)

@app.route('/api/employee/package/update', methods=['POST'])
def update_employee_package():
    """Update employee package"""
    if not session.get('employee_id'):
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        updates = {}
        
        # Validate and process updates
        for field, value in data.items():
            if field in ['basic_salary', 'provident_fund', 'car_allowance', 'bonus']:
                try:
                    updates[field] = float(value)
                except ValueError:
                    return jsonify({"error": f"Invalid value for {field}"}), 400
        
        # Update package
        updated_package = package_manager.update_employee_package(session['employee_id'], updates)
        if updated_package:
            return jsonify({
                "success": True,
                "package": updated_package,
                "message": "Package updated successfully"
            })
        else:
            return jsonify({"error": "Failed to update package"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/employee/package/submit', methods=['POST'])
def submit_employee_package():
    """Submit completed employee package"""
    if not session.get('employee_id'):
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        # Submit package
        submitted_package = package_manager.submit_employee_package(session['employee_id'])
        if submitted_package:
            # Create admin notification
            notification_manager.create_notification(
                type="PACKAGE_SUBMITTED",
                message=f"Employee {session['employee_id']} has submitted their package",
                admin_only=True
            )
            
            # Revoke employee access
            employee_access.revoke_employee_access(session['employee_id'])
            
            return jsonify({
                "success": True,
                "message": "Package submitted successfully. Your access has been revoked."
            })
        else:
            return jsonify({"error": "Failed to submit package"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/employee/calculate-net-pay', methods=['POST'])
def calculate_employee_net_pay():
    """Calculate net pay for employee package"""
    if not session.get('employee_id'):
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        package = package_manager.get_employee_package(session['employee_id'])
        if not package:
            return jsonify({"error": "Package not found"}), 404
        
        # Calculate net pay using existing SARS logic
        net_pay = calculate_randwater_net_pay(package['package_components'])
        
        return jsonify({
            "success": True,
            "net_pay": net_pay
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ============================================================================
# SUPER ADMIN PORTAL ROUTES
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
        
        # Super admin credentials (you only)
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
    
    # Get system statistics
    stats = {
        'total_randwater_admins': 3,
        'total_employees': len(employee_access.get_active_employees()),
        'total_packages': len(package_manager.get_all_packages()),
        'system_version': '2.0.0'
    }
    
    # Get recent activity
    recent_logins = []  # We'll implement this
    system_health = 'Excellent'
    
    return render_template('super_admin_dashboard.html',
                          stats=stats,
                          recent_logins=recent_logins,
                          system_health=system_health,
                          config=RANDWATER_CONFIG)

@app.route('/superadmin/calculation-tables')
def calculation_tables():
    """Manage calculation tables (SARS, Medical Aid, etc.)"""
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
                          tax_settings=tax_settings,
                          medical_aid_rates=medical_aid_rates,
                          tax_brackets=tax_brackets,
                          config=RANDWATER_CONFIG)

@app.route('/superadmin/user-management')
def user_management():
    """Manage Randwater admin users"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    # Mock admin users (we'll implement proper user management)
    admin_users = [
        {'id': 1, 'username': 'RandWaterAdmin', 'name': 'Primary Admin', 'status': 'Active', 'last_login': '2024-08-19'},
        {'id': 2, 'username': 'RandWaterAdmin2', 'name': 'Secondary Admin', 'status': 'Active', 'last_login': '2024-08-18'},
        {'id': 3, 'username': 'RandWaterAdmin3', 'name': 'Backup Admin', 'status': 'Inactive', 'last_login': '2024-08-15'}
    ]
    
    return render_template('user_management.html',
                          admin_users=admin_users,
                          config=RANDWATER_CONFIG)

@app.route('/superadmin/security-settings')
def security_settings():
    """Configure system security settings"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    # Security configuration
    security_config = {
        'session_timeout': 30,  # minutes
        'password_expiry': 90,  # days
        'max_login_attempts': 3,
        'account_lockout_duration': 15,  # minutes
        'require_2fa': False,
        'password_complexity': True,
        'audit_logging': True
    }
    
    return render_template('security_settings.html',
                          security_config=security_config,
                          config=RANDWATER_CONFIG)

# ============================================================================
# ADMIN PORTAL ROUTES (Enhanced)
# ============================================================================

@app.route('/admin/randwater', methods=['GET', 'POST'])
def randwater_admin_login():
    """Rand Water admin login"""
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
    """Enhanced Rand Water admin panel"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    # Get statistics
    active_employees = employee_access.get_active_employees()
    pending_submissions = employee_access.get_pending_submissions()
    submitted_packages = package_manager.get_submitted_packages()
    notifications = notification_manager.get_admin_notifications()
    
    # Calculate days remaining for pending submissions
    current_date = datetime.now()
    for employee in pending_submissions:
        if employee.get('access_expires'):
            try:
                expiry_date = datetime.fromisoformat(employee['access_expires'].replace('Z', '+00:00'))
                days_remaining = (expiry_date - current_date).days
                employee['days_remaining'] = max(0, days_remaining)
                employee['is_expired'] = days_remaining < 0
            except Exception as e:
                logger.error(f"Error calculating days remaining for {employee['employee_id']}: {str(e)}")
                employee['days_remaining'] = 0
                employee['is_expired'] = True
        else:
            employee['days_remaining'] = 0
            employee['is_expired'] = True
    
    stats = {
        'total_employees': len(active_employees),
        'pending_submissions': len(pending_submissions),
        'submitted_packages': len(submitted_packages),
        'company': 'RANDWATER'
    }
    
    return render_template('randwater_admin_panel_enhanced.html', 
                          stats=stats, 
                          active_employees=active_employees,
                          pending_submissions=pending_submissions,
                          submitted_packages=submitted_packages,
                          notifications=notifications,
                          current_date=current_date.strftime('%Y-%m-%d'),
                          config=RANDWATER_CONFIG)

@app.route('/admin/randwater/upload-sap', methods=['GET', 'POST'])
def upload_sap_data():
    """Upload SAP Excel data for employee packages"""
    if not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    if request.method == 'POST':
        if 'sap_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['sap_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith('.xlsx'):
            try:
                # Read Excel file
                logger.info(f"Reading Excel file: {file.filename}")
                df = pd.read_excel(file)
                logger.info(f"Excel file read successfully. Rows: {len(df)}, Columns: {len(df.columns)}")
                
                # Log column names for debugging
                logger.info(f"Excel columns: {list(df.columns)}")
                
                # Process employee data using actual SAP headers
                employee_data = []
                for index, row in df.iterrows():
                    try:
                        logger.info(f"Processing row {index + 1}: Employee {row.get('EMPLOYEECODE', 'UNKNOWN')}")
                        
                        employee_record = {
                            'EMPLOYEECODE': str(row.get('EMPLOYEECODE', '')),
                            'SURNAME': str(row.get('SURNAME', '')),
                            'FIRSTNAME': str(row.get('FIRSTNAME', '')),
                            'TITLE': str(row.get('TITLE', '')),
                            'BIRTHDATE': str(row.get('BIRTHDATE', '')),
                            'AGE': str(row.get('AGE', '')),
                            'RACE': str(row.get('RACE', '')),
                            'GENDER': str(row.get('GENDER', '')),
                            'DISABILITY': str(row.get('DISABILITY', '')),
                            'DATEENGAGED': str(row.get('DATEENGAGED', '')),
                            'YOS': str(row.get('YOS', '')),
                            'CostCenter': str(row.get('CostCenter', '')),
                            'PERSONNELAREADESCRIPTION': str(row.get('PERSONNELAREADESCRIPTION', '')),
                            'PERSONNELSUBAREADESCRIPTION': str(row.get('PERSONNELSUBAREADESCRIPTION', '')),
                            'EMPLOYEEGROUPDESCRIPTION': str(row.get('EMPLOYEEGROUPDESCRIPTION', '')),
                            'EMPLOYEESUBGROUPDESCRIPTION': str(row.get('EMPLOYEESUBGROUPDESCRIPTION', '')),
                            'JOBID': str(row.get('JOBID', '')),
                            'JOBSHORT': str(row.get('JOBSHORT', '')),
                            'JOBLONG': str(row.get('JOBLONG', '')),
                            'HAYUNIT': str(row.get('HAYUNIT', '')),
                            'POSITIONID': str(row.get('POSITIONID', '')),
                            'POSTIONSHORT': str(row.get('POSTIONSHORT', '')),
                            'POSITIONLONG': str(row.get('POSITIONLONG', '')),
                            'BAND': str(row.get('BAND', '')),
                            'PAYSCALELEVEL': str(row.get('PAYSCALELEVEL', '')),
                            'PORTFOLIO': str(row.get('PORTFOLIO', '')),
                            'DIVISION': str(row.get('DIVISION', '')),
                            'DEPARTMENT': str(row.get('DEPARTMENT', '')),
                            'ORGANIZATIONALUNIT': str(row.get('ORGANIZATIONALUNIT', '')),
                            'ORGANIZATIONALUNITLONG': str(row.get('ORGANIZATIONALUNITLONG', '')),
                            'TPE': safe_float_conversion(row.get('TPE', 0)),  # Total Pensionable Emolument
                            'CAR': safe_float_conversion(row.get('CAR', 0)),  # Car Allowance
                            'CASH': safe_float_conversion(row.get('CASH', 0)),  # Cash Allowance
                            'HOUSING': safe_float_conversion(row.get('HOUSING', 0)),  # Housing Allowance
                            'CRITICALSKILLS': safe_float_conversion(row.get('CRITICALSKILLS', 0)),
                            'pension': safe_float_conversion(row.get('pension', 0)),  # Pension/Provident Fund
                            'PENSIONOPTION': str(row.get('PENSIONOPTION', '')),
                            'PENSIONERCONTRIBUTION': safe_float_conversion(row.get('PENSIONERCONTRIBUTION', 0)),
                            'PENSIONEECONTRIBUTION': safe_float_conversion(row.get('PENSIONEECONTRIBUTION', 0)),
                            'CASHOPTION': str(row.get('CASHOPTION', '')),
                            'MEDICAL': safe_float_conversion(row.get('MEDICAL', 0)),  # Medical Aid
                            'MEDICALOPTION': str(row.get('MEDICALOPTION', '')),
                            'SPOUSE': str(row.get('SPOUSE', '')),
                            'CHILDREN': str(row.get('CHILDREN', '')),
                            'ADULTS': str(row.get('ADULTS', '')),
                            'MEDICALEECONTRIBUTION': safe_float_conversion(row.get('MEDICALEECONTRIBUTION', 0)),
                            'MEDICALERCONTRIBUTION': safe_float_conversion(row.get('MEDICALERCONTRIBUTION', 0)),
                            'UIF': safe_float_conversion(row.get('UIF', 0)),
                            'GROUPLIFEEECONTRIBUTION': safe_float_conversion(row.get('GROUPLIFEEECONTRIBUTION', 0)),
                            'GROUPLIFEERCONTRIBUTION': safe_float_conversion(row.get('GROUPLIFEERCONTRIBUTION', 0)),
                            'BONUSPROVISION': safe_float_conversion(row.get('BONUSPROVISION', 0)),  # Annual Bonus
                            'CTC': safe_float_conversion(row.get('CTC', 0)),  # Cost to Company
                            'TCTC': safe_float_conversion(row.get('TCTC', 0)),  # Total Cost to Company
                            'LQ': str(row.get('LQ', '')),
                            'MID': str(row.get('MID', '')),
                            'HQ': str(row.get('HQ', '')),
                            'LQPACKAGE': str(row.get('LQPACKAGE', '')),
                            'MIDPACKAGE': str(row.get('MIDPACKAGE', '')),
                            'HQPACKAGE': str(row.get('HQPACKAGE', '')),
                            'begda': str(row.get('begda', '')),
                            'endda': str(row.get('endda', '')),
                            'aedtm': str(row.get('aedtm', '')),
                            'CELLPHONEALLOWANCE': safe_float_conversion(row.get('CELLPHONEALLOWANCE', 0)),
                            'DATASERVICEALLOWANCE': safe_float_conversion(row.get('DATASERVICEALLOWANCE', 0))
                        }
                        
                        logger.info(f"Employee record created for {employee_record['EMPLOYEECODE']}")
                        employee_data.append(employee_record)
                        
                    except Exception as row_error:
                        logger.error(f"Error processing row {index + 1}: {str(row_error)}")
                        flash(f'Error processing row {index + 1}: {str(row_error)}', 'error')
                        continue
                
                logger.info(f"Total employee records processed: {len(employee_data)}")
                
                if not employee_data:
                    flash('No valid employee records found in the Excel file', 'error')
                    return redirect(request.url)
                
                # Upload to package manager
                upload_record = package_manager.upload_sap_data(
                    filename=secure_filename(file.filename),
                    upload_date=datetime.now().isoformat(),
                    employee_data=employee_data
                )
                
                # Create employee packages and access for O-Q band employees
                packages_created = 0
                access_created = 0
                
                # Get access period from form (default to 30 if not provided)
                access_period = int(request.form.get('accessPeriod', 30))
                logger.info(f"Setting access period to {access_period} days for all employees")
                
                # Log all unique bands found in the data
                unique_bands = set(employee['BAND'] for employee in employee_data)
                logger.info(f"Unique bands found in data: {unique_bands}")
                
                for employee in employee_data:
                    try:
                        # Check if band starts with O, P, or Q (handles O<, O2, P1, Q1, etc.)
                        band = str(employee['BAND']).strip().upper()
                        is_valid_band = any(band.startswith(prefix) for prefix in ['O', 'P', 'Q'])
                        
                        if is_valid_band:
                            logger.info(f"Processing employee {employee['EMPLOYEECODE']} (Band {employee['BAND']})")
                            
                            # Create employee access first
                            try:
                                access = employee_access.create_employee_access(
                                    employee['EMPLOYEECODE'],
                                    employee['BAND'],
                                    access_period
                                )
                                access_created += 1
                                logger.info(f"Access created for {employee['EMPLOYEECODE']}")
                            except Exception as e:
                                logger.error(f"Error creating access for {employee['EMPLOYEECODE']}: {str(e)}")
                                continue
                            
                            # Create package using TCTC as the limit
                            try:
                                package = package_manager.create_employee_package(
                                    employee['EMPLOYEECODE'],
                                    employee,
                                    employee['TCTC']
                                )
                                packages_created += 1
                                logger.info(f"Package created for {employee['EMPLOYEECODE']}")
                            except Exception as e:
                                logger.error(f"Error creating package for {employee['EMPLOYEECODE']}: {str(e)}")
                                continue
                        else:
                            logger.info(f"Skipping employee {employee['EMPLOYEECODE']} (Band {employee['BAND']}) - not O, P, or Q band")
                            
                    except Exception as e:
                        logger.error(f"Error processing employee {employee.get('EMPLOYEECODE', 'UNKNOWN')}: {str(e)}")
                        continue
                
                flash(f'Successfully uploaded {len(employee_data)} employee records. Created {packages_created} packages and {access_created} access accounts for O-Q band employees.', 'success')
                return redirect(url_for('randwater_admin_panel'))
                
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
                logger.error(f'SAP upload error: {str(e)}')
                return redirect(request.url)
        else:
            flash('Please upload an Excel (.xlsx) file', 'error')
            return redirect(request.url)
    
    return render_template('upload_sap_data.html', config=RANDWATER_CONFIG)

@app.route('/admin/randwater/clear-uploaded-data', methods=['POST'])
def clear_uploaded_data():
    """Clear all uploaded SAP data and employee access"""
    if not session.get('isRandWaterAdmin'):
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        # Clear SAP uploads
        package_manager.clear_sap_uploads()
        
        # Clear employee access
        employee_access.clear_all_access()
        
        # Clear employee packages
        package_manager.clear_all_packages()
        
        flash('All uploaded data has been cleared successfully', 'success')
        return jsonify({"success": True, "message": "All data cleared successfully"})
        
    except Exception as e:
        logger.error(f'Error clearing data: {str(e)}')
        flash(f'Error clearing data: {str(e)}', 'error')
        return jsonify({"error": str(e)}), 400

@app.route('/admin/randwater/export-packages')
def export_packages_for_sap():
    """Export submitted packages for SAP upload"""
    if not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        # Get export data
        export_data = package_manager.export_packages_for_sap()
        
        if not export_data:
            flash('No packages to export', 'warning')
            return redirect(url_for('randwater_admin_panel'))
        
        # Create Excel file
        df = pd.DataFrame(export_data)
        
        # Create output buffer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Packages', index=False)
        
        output.seek(0)
        
        # Generate filename
        filename = f"randwater_packages_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Error exporting packages: {str(e)}', 'error')
        return redirect(url_for('randwater_admin_panel'))

@app.route('/admin/randwater/employee-access')
def manage_employee_access():
    if not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        # Get all employees with access
        all_employees = employee_access.get_all_employees()
        
        # Calculate days remaining and expired status for each employee
        current_date = datetime.now()
        active_employees = []
        expired_employees = []
        
        for employee in all_employees:
            if employee.get('access_expires'):
                try:
                    expiry_date = datetime.fromisoformat(employee['access_expires'].replace('Z', '+00:00'))
                    days_remaining = (expiry_date - current_date).days
                    employee['days_remaining'] = max(0, days_remaining)
                    employee['is_expired'] = days_remaining < 0
                except Exception as e:
                    logger.error(f"Error calculating days remaining for {employee['employee_id']}: {str(e)}")
                    employee['days_remaining'] = 0
                    employee['is_expired'] = True
            else:
                employee['days_remaining'] = 0
                employee['is_expired'] = True
            
            # Check if employee has a package
            package = package_manager.get_employee_package(employee['employee_id'])
            employee['package_submitted'] = package is not None
            
            if employee['is_expired']:
                expired_employees.append(employee)
            else:
                active_employees.append(employee)
        
        # Calculate statistics
        total_employees = len(all_employees)
        active_access = len(active_employees)
        expired_access = len(expired_employees)
        pending_submissions = len([e for e in active_employees if not e['package_submitted']])
        
        # Get company info for logo
        company_info = RANDWATER_CONFIG # Assuming RANDWATER_CONFIG is the source of company info
        
        # Prepare date variables for the template
        today = datetime.now()
        default_end = today + timedelta(days=30)
        
        stats = {
            'total_employees': total_employees,
            'active_access': active_access,
            'expired_access': expired_access,
            'pending_submissions': pending_submissions,
            'company': company_info
        }
        
        return render_template('manage_employee_access.html',
                             active_employees=active_employees,
                             expired_employees=expired_employees,
                             stats=stats,
                             config=company_info,
                             today_date=today.strftime('%Y-%m-%d'),
                             default_end_date=default_end.strftime('%Y-%m-%d'))
                             
    except Exception as e:
        logger.error(f'Error in manage_employee_access: {str(e)}')
        flash(f'Error loading employee access data: {str(e)}', 'error')
        return redirect(url_for('randwater_admin_panel'))

@app.route('/admin/randwater/employee-details/<employee_id>')
def get_employee_details(employee_id):
    """Get detailed employee information including package data"""
    if not session.get('isRandWaterAdmin'):
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        # Get employee access information
        employee_access_data = None
        for access in employee_access.access_data:
            if access['employee_id'] == employee_id:
                employee_access_data = access
                break
        
        if not employee_access_data:
            return jsonify({"error": "Employee not found"}), 404
        
        # Get employee package information
        package_data = package_manager.get_employee_package(employee_id)
        
        return jsonify({
            "success": True,
            "employee": employee_access_data,
            "package": package_data
        })
        
    except Exception as e:
        logger.error(f'Error getting employee details: {str(e)}')
        return jsonify({"error": str(e)}), 400

# ============================================================================
# SALARY SIMULATOR ROUTES (Net Pay Modeler)
# ============================================================================

@app.route('/admin/salary-simulator')
def salary_simulator():
    """Salary Simulator for administrators"""
    if not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    return render_template('salary_simulator.html', config=RANDWATER_CONFIG)

@app.route('/api/salary-simulator/calculate', methods=['POST'])
def calculate_salary_simulation():
    """Calculate salary simulation"""
    if not session.get('isRandWaterAdmin'):
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        
        # Calculate net pay using existing logic
        net_pay = calculate_randwater_net_pay(data)
        
        return jsonify({
            "success": True,
            "net_pay": net_pay
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def calculate_randwater_net_pay(package_data: Dict) -> Dict:
    """Calculate net pay based on package data using SARS rules"""
    try:
        settings = load_tax_settings()
        
        # Extract values
        basic_salary = float(package_data.get('basic_salary', 0))
        car_allowance = float(package_data.get('car_allowance', 0))
        cellphone_allowance = float(package_data.get('cellphone_allowance', 0))
        data_service_allowance = float(package_data.get('data_service_allowance', 0))
        housing_allowance = float(package_data.get('housing_allowance', 0))
        medical_aid = float(package_data.get('medical_aid', 0))
        bonus = float(package_data.get('bonus', 0))
        provident_fund = float(package_data.get('provident_fund', 0))
        
        # Calculate gross pay
        gross = (basic_salary + car_allowance + cellphone_allowance + 
                data_service_allowance + housing_allowance + medical_aid + bonus)
        
        # Calculate deductions
        total_deductions = 0
        total_employer = 0
        total_randwater_benefits = 0
        
        # UIF calculation
        uif = min(gross * 0.01, settings['uif_ceiling'])
        total_deductions += uif
        
        # Provident fund
        if provident_fund > 0:
            total_deductions += provident_fund
        
        # Tax calculation
        annual_income = gross * 12
        annual_tax = calculate_tax(annual_income, settings)
        
        # Medical tax credits
        has_medical = medical_aid > 0
        dependants = 0  # This would come from form data
        
        if has_medical:
            credit = settings['medical_main']
            if dependants >= 1:
                credit += settings['medical_first']
            if dependants > 1:
                credit += (dependants - 1) * settings['medical_additional']
            annual_tax -= credit * 12
        
        annual_tax = max(0, annual_tax)
        monthly_tax = round(annual_tax / 12, 2)
        total_deductions += monthly_tax
        
        net_pay = gross - total_deductions
        
        return {
            "earnings": gross,
            "deductions": total_deductions,
            "employer": total_employer,
            "randwater_benefits": total_randwater_benefits,
            "uif": round(uif, 2),
            "monthly_tax": monthly_tax,
            "take_home": round(net_pay, 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating net pay: {str(e)}")
        return {"error": str(e)}

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

def send_email(recipients: List[str], subject: str, body: str, operation_type: str = "notification") -> Dict[str, any]:
    """Send email using configured SMTP settings"""
    if not smtp_config.config['enabled']:
        error_msg = "SMTP is not configured or enabled"
        email_logger.log_email_operation(operation_type, recipients, subject, False, body, error_msg)
        return {'success': False, 'error': error_msg}
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Create message
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = f"{smtp_config.config['from_name']} <{smtp_config.config['from_email']}>"
        msg['To'] = ', '.join(recipients)
        
        # Add body
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server
        if smtp_config.config['use_tls']:
            server = smtplib.SMTP(smtp_config.config['smtp_server'], smtp_config.config['smtp_port'])
            server.starttls()
        else:
            server = smtplib.SMTP(smtp_config.config['smtp_server'], smtp_config.config['smtp_port'])
        
        # Login
        server.login(smtp_config.config['username'], smtp_config.config['password'])
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        # Log successful email
        email_logger.log_email_operation(operation_type, recipients, subject, True, body)
        
        return {'success': True, 'message': f'Email sent successfully to {len(recipients)} recipient(s)'}
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error sending email: {error_msg}")
        email_logger.log_email_operation(operation_type, recipients, subject, False, body, error_msg)
        return {'success': False, 'error': error_msg}


@app.route('/admin/randwater/bulk-email-credentials', methods=['POST'])
def bulk_email_credentials():
    """Send login credentials to selected employees"""
    if not session.get('isRandWaterAdmin'):
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        employee_ids = data.get('employee_ids', [])
        
        if not employee_ids:
            return jsonify({"success": False, "error": "No employees selected"})
        
        # Get employee details
        employees = []
        for emp_id in employee_ids:
            employee = employee_access.get_employee_by_id(emp_id)
            if employee:
                employees.append(employee)
        
        if not employees:
            return jsonify({"success": False, "error": "No valid employees found"})
        
        # Prepare email content
        subject = "Your Rand Water Package Builder Login Credentials"
        
        success_count = 0
        failed_count = 0
        failed_employees = []
        
        for employee in employees:
            # Create personalized email body
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #0066CC 0%, #00A3E0 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                        <h1 style="margin: 0;">Rand Water Package Builder</h1>
                        <p style="margin: 10px 0 0 0;">Your Access Credentials</p>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h2 style="color: #0066CC; margin-top: 0;">Hello!</h2>
                        <p>Your access to the Rand Water Package Builder system has been granted.</p>
                        
                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #0066CC; margin: 20px 0;">
                            <h3 style="color: #0066CC; margin-top: 0;">Login Information</h3>
                            <p><strong>Employee ID:</strong> {employee['employee_id']}</p>
                            <p><strong>Username:</strong> {employee['username']}</p>
                            <p><strong>Password:</strong> {employee['password']}</p>
                        </div>
                        
                        <div style="background: #e6f3ff; padding: 15px; border-radius: 8px; border: 1px solid #0066CC;">
                            <h4 style="color: #0066CC; margin-top: 0;">Access Details</h4>
                            <p><strong>Access Granted:</strong> {employee.get('access_granted', 'N/A')}</p>
                            <p><strong>Access Expires:</strong> {employee.get('access_expires', 'N/A')}</p>
                        </div>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border: 1px solid #ffc107;">
                        <h4 style="color: #856404; margin-top: 0;">Important Notes</h4>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Keep your credentials secure and do not share them with others</li>
                            <li>Access expires on the specified date - contact your administrator if you need an extension</li>
                            <li>For technical support, contact your system administrator</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px; color: #666; font-size: 12px;">
                        <p>This is an automated message from the Rand Water Package Builder system.</p>
                        <p>Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Send email to employee (in real implementation, you'd use their actual email)
            # For now, we'll log it as if it was sent successfully
            result = send_email(
                recipients=[f"{employee['username']}@randwater.co.za"],  # Placeholder email
                subject=subject,
                body=body,
                operation_type="credentials"
            )
            
            if result['success']:
                success_count += 1
            else:
                failed_count += 1
                failed_employees.append({
                    'employee_id': employee['employee_id'],
                    'error': result['error']
                })
        
        # Prepare response
        response = {
            "success": True,
            "message": f"Email operation completed. {success_count} successful, {failed_count} failed.",
            "details": {
                "total_employees": len(employees),
                "successful": success_count,
                "failed": failed_count,
                "failed_details": failed_employees
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f'Error in bulk_email_credentials: {str(e)}')
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/randwater/email-logs')
def email_logs():
    """View email logs"""
    if not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        # Get filter parameters
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        operation_type = request.args.get('operation_type', '')
        
        # Get logs based on filters
        if start_date and end_date:
            logs = email_logger.get_logs_by_date_range(start_date, end_date)
        elif operation_type:
            logs = email_logger.get_logs_by_operation(operation_type)
        else:
            logs = email_logger.logs
        
        # Get success rate statistics
        success_stats = email_logger.get_success_rate()
        
        # Get company info for logo
        company_info = RANDWATER_CONFIG
        
        return render_template('email_logs.html',
                             logs=logs,
                             success_stats=success_stats,
                             config=company_info,
                             start_date=start_date,
                             end_date=end_date,
                             operation_type=operation_type)
                             
    except Exception as e:
        logger.error(f'Error in email_logs: {str(e)}')
        flash(f'Error loading email logs: {str(e)}', 'error')
        return redirect(url_for('randwater_admin_panel'))


@app.route('/admin/randwater/email-logs/download')
def download_email_logs():
    """Download email logs as CSV"""
    if not session.get('isRandWaterAdmin'):
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        # Get filter parameters
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        operation_type = request.args.get('operation_type', '')
        
        # Get logs based on filters
        if start_date and end_date:
            logs = email_logger.get_logs_by_date_range(start_date, end_date)
        elif operation_type:
            logs = email_logger.get_logs_by_operation(operation_type)
        else:
            logs = email_logger.logs
        
        # Generate CSV
        csv_content = email_logger.export_logs_csv(logs)
        
        if not csv_content:
            return jsonify({"error": "No logs to export"}), 404
        
        # Create response
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=email_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f'Error downloading email logs: {str(e)}')
        return jsonify({"error": str(e)}), 500


@app.route('/admin/randwater/smtp-config', methods=['GET', 'POST'])
def smtp_config_management():
    """Manage SMTP configuration"""
    if not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            new_config = {
                'smtp_server': request.form.get('smtp_server', ''),
                'smtp_port': int(request.form.get('smtp_port', 587)),
                'use_tls': request.form.get('use_tls') == 'on',
                'username': request.form.get('username', ''),
                'password': request.form.get('password', ''),
                'from_email': request.form.get('from_email', ''),
                'from_name': request.form.get('from_name', ''),
                'enabled': request.form.get('enabled') == 'on'
            }
            
            # Update configuration
            smtp_config.update_config(new_config)
            
            flash('SMTP configuration updated successfully', 'success')
            return redirect(url_for('smtp_config_management'))
            
        except Exception as e:
            logger.error(f'Error updating SMTP config: {str(e)}')
            flash(f'Error updating SMTP configuration: {str(e)}', 'error')
    
    # GET request - show current configuration
    try:
        current_config = smtp_config.get_config()
        company_info = RANDWATER_CONFIG
        
        return render_template('smtp_config.html',
                             config=company_info,
                             smtp_config=current_config)
                             
    except Exception as e:
        logger.error(f'Error loading SMTP config: {str(e)}')
        flash(f'Error loading SMTP configuration: {str(e)}', 'error')
        return redirect(url_for('randwater_admin_panel'))


@app.route('/admin/randwater/smtp-test', methods=['POST'])
def test_smtp_connection():
    """Test SMTP connection"""
    if not session.get('isRandWaterAdmin'):
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        result = smtp_config.test_connection()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'Error testing SMTP connection: {str(e)}')
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/admin/randwater/clear-email-logs', methods=['POST'])
def clear_email_logs():
    """Clear all email logs"""
    if not session.get('isRandWaterAdmin'):
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        email_logger.clear_logs()
        return jsonify({"success": True, "message": "Email logs cleared successfully"})
        
    except Exception as e:
        logger.error(f'Error clearing email logs: {str(e)}')
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/randwater/manage-packages')
def manage_packages():
    """Manage all employee packages"""
    if not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        # Get all packages
        packages = package_manager.get_all_packages()
        
        # Get employee access info for additional context
        all_access = employee_access.get_all_employees()
        
        # Create a mapping of employee_id to access info
        access_map = {access['employee_id']: access for access in all_access}
        
        # Enhance packages with employee info
        enhanced_packages = []
        for package in packages:
            employee_info = access_map.get(package['employee_id'], {})
            enhanced_package = {
                **package,
                'employee_name': f"{employee_info.get('first_name', '')} {employee_info.get('surname', '')}".strip(),
                'grade_band': employee_info.get('grade_band', ''),
                'access_status': 'ACTIVE' if not employee_info.get('is_expired', True) else 'INACTIVE',
                'access_expires': employee_info.get('access_expiry_date', ''),
                'current_tctc': package_manager._calculate_tctc(package['package_components']),
                'is_submitted': package.get('status') == 'SUBMITTED'
            }
            enhanced_packages.append(enhanced_package)
        
        return render_template('manage_packages.html', 
                             packages=enhanced_packages,
                             config=RANDWATER_CONFIG)
    except Exception as e:
        logger.error(f"Error in manage_packages: {e}")
        flash(f'Error loading packages: {str(e)}', 'error')
        return redirect(url_for('randwater_admin_panel'))

@app.route('/admin/randwater/package-analytics')
def package_analytics():
    """View package analytics and statistics"""
    if not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    try:
        # Get all packages for analytics
        packages = package_manager.get_all_packages()
        
        # Calculate analytics
        total_packages = len(packages)
        submitted_packages = len([p for p in packages if p.get('status') == 'SUBMITTED'])
        pending_packages = total_packages - submitted_packages
        
        # TCTC distribution
        tctc_values = [package_manager._calculate_tctc(p['package_components']) for p in packages]
        avg_tctc = sum(tctc_values) / len(tctc_values) if tctc_values else 0
        
        # Grade band distribution
        all_access = employee_access.get_all_employees()
        grade_counts = {}
        for access in all_access:
            grade = access.get('grade_band', 'Unknown')
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        analytics = {
            'total_packages': total_packages,
            'submitted_packages': submitted_packages,
            'pending_packages': pending_packages,
            'avg_tctc': avg_tctc,
            'grade_distribution': grade_counts,
            'tctc_range': {
                'min': min(tctc_values) if tctc_values else 0,
                'max': max(tctc_values) if tctc_values else 0
            }
        }
        
        return render_template('package_analytics.html', 
                             analytics=analytics,
                             config=RANDWATER_CONFIG)
    except Exception as e:
        logger.error(f"Error in package_analytics: {e}")
        flash(f'Error loading analytics: {str(e)}', 'error')
        return redirect(url_for('randwater_admin_panel'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
