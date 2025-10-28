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
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

# Dynamic user credentials storage (DEPRECATED - kept for backward compatibility)
# Now using system_users.json instead
USER_CREDENTIALS = {
    'superadmin': {'password': 'SuperAdmin2024!', 'user_type': 'super_admin'},
    'RandWaterAdmin': {'password': 'RandWater2024!', 'user_type': 'randwater_admin'}
}

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
    return redirect(url_for('unified_login'))

@app.route('/employee/package-builder')
def employee_package_builder():
    """Main Package Builder interface for employees"""
    if not session.get('employee_id'):
        return redirect(url_for('employee_login'))
    
    # Get employee's package
    package = package_manager.get_employee_package(session['employee_id'])
    if not package:
        flash('No package found for your employee ID. Please contact HR.', 'warning')
        # Create minimal package to prevent redirect loop
        package = {
            'employee_id': session['employee_id'],
            'sap_data': {},
            'package_components': {
                'basic_salary': 0,
                'car_allowance': 0,
                'provident_fund': 0,
                'bonus': 0
            },
            'current_tctc': 0,
            'tctc_limit': 0
        }
    
    # Get notifications
    notifications = notification_manager.get_employee_notifications(session['employee_id'])
    
    return render_template('employee_package_builder.html', 
                         package=package, 
                         notifications=notifications,
                         config=RANDWATER_CONFIG)

@app.route('/api/employee/package/update', methods=['POST'])
def update_employee_package():
    """Update employee package with budget validation"""
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
        
        # Update package with budget validation
        result = package_manager.update_employee_package(session['employee_id'], updates)
        
        if result['success']:
            response = {
                "success": True,
                "package": result['package'],
                "message": "Package updated successfully"
            }
            
            # Include warnings if any
            if result.get('warnings'):
                response['warnings'] = result['warnings']
            
            # Include auto-adjustments if any
            if result.get('auto_adjustments'):
                response['auto_adjustments'] = result['auto_adjustments']
                response['message'] += " (Some values were auto-adjusted to fit budget constraints)"
            
            return jsonify(response)
        else:
            return jsonify({"error": result['error']}), 400
            
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
    """Super Admin login - redirects to unified login"""
    # Redirect to unified login for consistent authentication
    return redirect(url_for('unified_login'))

@app.route('/superadmin/logout')
def super_admin_logout():
    """Super Admin logout"""
    session.pop('isSuperAdmin', None)
    session.pop('superadmin_username', None)
    return redirect(url_for('unified_login'))

@app.route('/superadmin/dashboard')
def super_admin_dashboard():
    """Super Admin dashboard for system configuration"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    # Get system statistics
    total_superadmins = len([u for u in USER_CREDENTIALS.values() if u['user_type'] == 'super_admin'])
    total_randwater_admins = len([u for u in USER_CREDENTIALS.values() if u['user_type'] == 'randwater_admin'])
    total_employees = len(employee_access.get_all_employees())  # All employees, not just active
    
    stats = {
        'total_superadmins': total_superadmins,
        'total_randwater_admins': total_randwater_admins,
        'total_employees': total_employees,
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
    
    # Load SMTP settings
    smtp_settings = load_smtp_settings()
    
    return render_template('calculation_tables.html',
                          tax_settings=tax_settings,
                          medical_aid_rates=medical_aid_rates,
                          tax_brackets=tax_brackets,
                          smtp_settings=smtp_settings,
                          config=RANDWATER_CONFIG)

@app.route('/superadmin/system-security')
def system_security():
    """System Security Management"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    security_settings = load_security_settings()
    return render_template('system_security.html',
                          security_settings=security_settings,
                          config=RANDWATER_CONFIG)

@app.route('/superadmin/system-backup')
def system_backup():
    """System Backup Management"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    backups = get_backup_list()
    return render_template('system_backup.html',
                          backups=backups,
                          config=RANDWATER_CONFIG)

@app.route('/superadmin/system-analytics')
def system_analytics():
    """System Analytics Dashboard"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    analytics = get_system_analytics()
    return render_template('system_analytics.html',
                          analytics=analytics,
                          config=RANDWATER_CONFIG)

@app.route('/superadmin/user-management')
def user_management():
    """Manage Randwater admin users"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('super_admin_login'))
    
    # Mock admin users (we'll implement proper user management)
    admin_users = [
        {'id': 1, 'username': 'RandWaterAdmin', 'name': 'Annelise', 'full_name': 'Annelise', 'email': 'annelise@smarthr.co.za', 'role': 'admin', 'profile': 'admin', 'status': 'active', 'last_login': '2025-09-01'},
        {'id': 2, 'username': 'RandWaterAdmin2', 'name': 'Secondary Admin', 'full_name': 'Secondary Admin', 'email': 'admin2@smarthr.co.za', 'role': 'admin', 'profile': 'admin', 'status': 'active', 'last_login': '2025-08-30'},
        {'id': 3, 'username': 'RandWaterAdmin3', 'name': 'Backup Admin', 'full_name': 'Backup Admin', 'email': 'admin3@smarthr.co.za', 'role': 'admin', 'profile': 'admin', 'status': 'inactive', 'last_login': '2025-08-15'}
    ]
    
    return render_template('user_management.html',
                          admin_users=admin_users,
                          users=admin_users,  # Template expects 'users' variable
                          config=RANDWATER_CONFIG)

@app.route('/superadmin/user-management/update/<int:user_id>', methods=['POST'])
def update_user(user_id):
    """Update user information"""
    if not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            # Fallback to form data if no JSON
            data = request.form.to_dict()
        
        username = data.get('username')
        full_name = data.get('full_name')
        email = data.get('email') 
        user_profile = data.get('user_profile')
        status = data.get('status')
        new_password = data.get('new_password')
        
        # Debug logging
        logger.info(f"Data received: username='{username}', full_name='{full_name}', email='{email}', profile='{user_profile}', status='{status}'")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Raw data: {data}")
        
        if not username or not full_name:
            return jsonify({'error': 'Username and Full Name are required'}), 400
        
        # Update the credentials in memory if password is provided
        if new_password and username in USER_CREDENTIALS:
            USER_CREDENTIALS[username]['password'] = new_password
            success_message = f'User {username} updated successfully! Password and credentials have been updated.'
        else:
            success_message = f'User {username} profile updated successfully! Note: No password change was made.'
        
        return jsonify({
            'success': True, 
            'message': success_message,
            'user': {
                'id': user_id,
                'username': username,
                'full_name': full_name,
                'email': email,
                'profile': user_profile,
                'status': status
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        return jsonify({'error': f'Error updating user: {str(e)}'}), 500

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
# UNIFIED LOGIN SYSTEM
# ============================================================================

@app.route('/')
def index():
    """Root route - redirect to unified login"""
    return redirect(url_for('unified_login'))

@app.route('/login', methods=['GET', 'POST'])
def unified_login():
    """Unified login for all user types"""
    if request.method == 'POST':
        raw_username = request.form.get('username') or ''
        username = raw_username.strip().lower()
        password = (request.form.get('password') or '').strip()
        
        if not username or not password:
            return render_template('unified_login.html', 
                                 error="Please enter both username and password", 
                                 config=RANDWATER_CONFIG)
        
        # Load system users and check credentials
        system_users = load_system_users()
        
        # DEBUG: Print comprehensive login debugging info
        print(f"\n=== PACKAGE BUILDER LOGIN DEBUG START ===")
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
        except Exception as e:
            print(f"Logger error: {e}")
        
        user_found = False
        username_matched = False
        
        # Check system users (super admin and randwater admin)
        for user in system_users:
            stored_pw = user.get('password', '')
            is_hashed = isinstance(stored_pw, str) and (':' in stored_pw)
            valid = (stored_pw == password)
            db_username = str(user.get('username', '')).strip().lower()
            
            if db_username == username:
                username_matched = True
                if not valid and is_hashed:
                    try:
                        valid = check_password_hash(stored_pw, password)
                    except Exception:
                        valid = False
            
            if db_username == username and valid:
                if user['status'] != 'active':
                    return render_template('unified_login.html', 
                                         error="Account is inactive. Please contact administrator.", 
                                         config=RANDWATER_CONFIG)
                
                # Update last login
                user['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                save_system_users(system_users)
                
                # Set session based on profile
                if user['profile'] == 'superadmin':
                    session['admin'] = True
                    session['isSuperAdmin'] = True
                    session['user_type'] = 'super_admin'
                    session['username'] = username
                    logger.info(f"Super Admin {username} logged in successfully")
                    flash('Welcome Super Admin!', 'success')
                    return redirect(url_for('super_admin_dashboard'))
                
                elif user['profile'] == 'admin':
                    session['admin'] = True
                    session['isRandWaterAdmin'] = True
                    session['user_type'] = 'randwater_admin'
                    session['username'] = username
                    logger.info(f"Randwater Admin {username} logged in successfully")
                    flash('Welcome RandWater Admin!', 'success')
                    return redirect(url_for('randwater_admin_panel'))
                
                else:
                    user_found = True
                    break
        
        # If username matched but password invalid, show specific error
        if not user_found and username_matched:
            return render_template('unified_login.html', 
                                 error="Invalid password", 
                                 config=RANDWATER_CONFIG)
        
        # If no system user found, check employees
        if not user_found:
            employee_data = employee_access.validate_employee_access(username, password)
            if employee_data:
                session['employee_id'] = username
                session['user_type'] = 'employee'
                flash('Welcome to Package Builder!', 'success')
                return redirect(url_for('employee_package_builder'))
            else:
                return render_template('unified_login.html', 
                                     error="Invalid username or password", 
                                     config=RANDWATER_CONFIG)
    
    # GET request - show login form
    return render_template('unified_login.html', config=RANDWATER_CONFIG)

@app.route('/logout')
def logout():
    """Unified logout for all user types"""
    user_type = session.get('user_type', 'unknown')
    session.clear()
    flash(f'You have been logged out successfully', 'info')
    return redirect(url_for('unified_login'))

@app.route('/employee/dashboard/<employee_id>')
def employee_dashboard(employee_id):
    """Employee dashboard"""
    if not session.get('isEmployee') or session.get('employee_id') != employee_id:
        flash('Please log in as an employee to access this page', 'error')
        return redirect(url_for('unified_login'))
    
    try:
        # Get employee package data
        package = package_manager.get_employee_package(employee_id)
        employee_data = session.get('employee_data', {})
        
        # Get SAP data for the employee
        sap_data = package_manager.get_sap_data_for_employee(employee_id)
        
        return render_template('employee_dashboard.html',
                             employee=employee_data,
                             package=package,
                             sap_data=sap_data,
                             config=RANDWATER_CONFIG)
    except Exception as e:
        logger.error(f"Error in employee dashboard for {employee_id}: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('unified_login'))

# ============================================================================
# ADMIN PORTAL ROUTES (Enhanced)
# ============================================================================

@app.route('/admin/randwater', methods=['GET', 'POST'])
def randwater_admin_login():
    """Rand Water admin login - redirects to unified login"""
    # Redirect to unified login for consistent authentication
    return redirect(url_for('unified_login'))



@app.route('/admin/randwater/dashboard')
def randwater_admin_panel():
    """Enhanced Rand Water admin panel"""
    if not session.get('admin') and not session.get('isRandWaterAdmin') and not session.get('isSuperAdmin'):
        return redirect(url_for('unified_login'))
    
    try:
        # Get statistics
        active_employees = employee_access.get_active_employees()
        pending_submissions = employee_access.get_pending_submissions()
        submitted_packages = package_manager.get_submitted_packages()
        notifications = notification_manager.get_admin_notifications()
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        # Provide default values if there are errors
        active_employees = []
        pending_submissions = []
        submitted_packages = []
        notifications = []
    
    # Enhance active employees with package data
    enhanced_active_employees = []
    for employee in active_employees:
        try:
            # Get employee package
            package = package_manager.get_employee_package(employee['employee_id'])
            
            # Get SAP data if available
            sap_data = package_manager.get_sap_data_for_employee(employee['employee_id']) if package else {}
            
            enhanced_employee = {
                **employee,
                'first_name': sap_data.get('FIRSTNAME', '') if sap_data else '',
                'surname': sap_data.get('SURNAME', '') if sap_data else '',
                'basic_salary': package['package_components']['basic_salary'] if package and package.get('package_components') else 0,
                'ctc': package['current_tctc'] if package and package.get('current_tctc') else 0,
                'department': sap_data.get('DEPARTMENT', 'N/A') if sap_data else 'N/A',
                'job_title': sap_data.get('JOBLONG', 'N/A') if sap_data else 'N/A',
                'package_submitted': package is not None and package.get('status') == 'SUBMITTED'
            }
            enhanced_active_employees.append(enhanced_employee)
        except Exception as e:
            logger.error(f"Error enhancing employee {employee.get('employee_id', 'Unknown')}: {str(e)}")
            # Add employee with basic info only
            enhanced_active_employees.append({
                **employee,
                'first_name': '',
                'surname': '',
                'basic_salary': 0,
                'ctc': 0,
                'department': 'N/A',
                'job_title': 'N/A',
                'package_submitted': False
            })
    
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
        'total_employees': len(enhanced_active_employees),
        'pending_submissions': len(pending_submissions),
        'submitted_packages': len(submitted_packages),
        'company': 'RANDWATER'
    }
    
    return render_template('randwater_admin_panel_enhanced.html', 
                          stats=stats, 
                          active_employees=enhanced_active_employees,
                          pending_submissions=pending_submissions,
                          submitted_packages=submitted_packages,
                          notifications=notifications,
                          current_date=current_date.strftime('%Y-%m-%d'),
                          config=RANDWATER_CONFIG)

@app.route('/admin/randwater/upload-sap', methods=['GET', 'POST'])
def upload_sap_data():
    """Upload SAP Excel data for employee packages"""
    if not (session.get('isRandWaterAdmin') or session.get('isSuperAdmin')):
        return redirect(url_for('unified_login'))
    
    if request.method == 'POST':
        if 'sap_file' not in request.files:
            error_msg = 'No file selected'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': error_msg})
            flash(error_msg, 'error')
            return redirect(request.url)
        
        file = request.files['sap_file']
        if file.filename == '':
            error_msg = 'No file selected'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': error_msg})
            flash(error_msg, 'error')
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
                
                success_message = f'Successfully uploaded {len(employee_data)} employee records. Created {packages_created} packages and {access_created} access accounts for O-Q band employees.'
                
                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': True,
                        'message': success_message,
                        'filename': file.filename,
                        'records_processed': len(employee_data),
                        'packages_created': packages_created,
                        'access_created': access_created
                    })
                else:
                    flash(success_message, 'success')
                    return redirect(url_for('randwater_admin_panel'))
                
            except Exception as e:
                error_message = f'Error processing file: {str(e)}'
                logger.error(f'SAP upload error: {str(e)}')
                
                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'error': error_message
                    })
                else:
                    flash(error_message, 'error')
                    return redirect(request.url)
        else:
            error_msg = 'Please upload an Excel (.xlsx) file'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': error_msg})
            flash(error_msg, 'error')
            return redirect(request.url)
    
    return render_template('upload_sap_data.html', config=RANDWATER_CONFIG)

@app.route('/admin/randwater/clear-uploaded-data', methods=['POST'])
def clear_uploaded_data():
    """Clear all uploaded SAP data and employee access"""
    if not (session.get('isRandWaterAdmin') or session.get('isSuperAdmin')):
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
    if not (session.get('isRandWaterAdmin') or session.get('isSuperAdmin')):
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
    if not (session.get('isRandWaterAdmin') or session.get('isSuperAdmin')):
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
    if not (session.get('isRandWaterAdmin') or session.get('isSuperAdmin')):
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
    if not (session.get('isRandWaterAdmin') or session.get('isSuperAdmin')):
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
    if not (session.get('isRandWaterAdmin') or session.get('isSuperAdmin')):
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
    if not (session.get('isRandWaterAdmin') or session.get('isSuperAdmin')):
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
    if not (session.get('isRandWaterAdmin') or session.get('isSuperAdmin')):
        return redirect(url_for('unified_login'))
    
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

@app.route('/package_view/<employee_id>')
def package_view(employee_id):
    """Rand Water Admin - View package details with edit capabilities"""
    if not session.get('admin') and not session.get('isRandWaterAdmin') and not session.get('isSuperAdmin'):
        return redirect(url_for('unified_login'))
    
    try:
        # Get employee package data
        package = package_manager.get_employee_package(employee_id)
        if not package:
            flash(f'Package not found for employee {employee_id}', 'error')
            return redirect(url_for('manage_packages'))
        
        # Debug: Log package structure
        logger.info(f"Package structure for {employee_id}: {package}")
        
        # Get employee access info
        employee_access_info = employee_access.get_employee_by_id(employee_id)
        if not employee_access_info:
            flash(f'Employee access not found for {employee_id}', 'error')
            return redirect(url_for('manage_packages'))
        
        # Get SAP data for the employee
        sap_data = package_manager.get_sap_data_for_employee(employee_id)
        
        # Debug: Log SAP data
        logger.info(f"SAP data for {employee_id}: {sap_data}")
        print(f"DEBUG: Package for {employee_id}: {package}")
        print(f"DEBUG: SAP data for {employee_id}: {sap_data}")
        
        # Create employee object for template
        employee = {
            'employee_id': employee_id,
            'first_name': sap_data.get('FIRSTNAME', '') if sap_data else '',
            'surname': sap_data.get('SURNAME', '') if sap_data else '',
            'grade_band': sap_data.get('BAND', 'O-Q') if sap_data else 'O-Q',
            'department': sap_data.get('DEPARTMENT', 'General') if sap_data else 'General',
            'job_title': sap_data.get('JOBLONG', 'Employee') if sap_data else 'Employee',
            'basic_salary': package['package_components'].get('basic_salary', 0) if package.get('package_components') else 0,
            'package': package,
            'sap_data': sap_data
        }
        
        # Get audit trail for this package
        audit_trail = package_manager.get_employee_audit_trail(employee_id)
        
        # Admin view - no notifications
        notifications = []
        
        return render_template('package_view_edit.html', 
                             config=RANDWATER_CONFIG,
                             employee=employee,
                             audit_trail=audit_trail,
                             notifications=notifications)
        
    except Exception as e:
        logger.error(f"Error viewing package for {employee_id}: {str(e)}")
        flash(f'Error viewing package: {str(e)}', 'error')
        return redirect(url_for('manage_packages'))

@app.route('/api/admin/package/<employee_id>')
def get_package_for_edit(employee_id):
    """Get package data for admin editing"""
    if not session.get('admin') and not session.get('isRandWaterAdmin') and not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        package = package_manager.get_employee_package(employee_id)
        if not package:
            return jsonify({'success': False, 'error': 'Package not found'})
        
        return jsonify({
            'success': True,
            'package': package
        })
    except Exception as e:
        logger.error(f"Error getting package for {employee_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/package/<employee_id>/audit')
def get_package_audit_trail(employee_id):
    """Get audit trail for package changes"""
    if not session.get('admin') and not session.get('isRandWaterAdmin') and not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Load audit trail from file or database
        audit_file = 'package_audit.json'
        audit_trail = []
        
        if os.path.exists(audit_file):
            with open(audit_file, 'r') as f:
                all_audits = json.load(f)
                audit_trail = [audit for audit in all_audits if audit.get('employee_id') == employee_id]
        
        return jsonify({
            'success': True,
            'audit_trail': audit_trail
        })
    except Exception as e:
        logger.error(f"Error getting audit trail for {employee_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/package/<employee_id>/update', methods=['POST'])
def update_package_admin(employee_id):
    """Update package as admin with audit trail"""
    if not session.get('admin') and not session.get('isRandWaterAdmin') and not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        package_components = data.get('package_components', {})
        change_summary = data.get('change_summary', '')
        
        # Get current package
        current_package = package_manager.get_employee_package(employee_id)
        if not current_package:
            return jsonify({'success': False, 'error': 'Package not found'})
        
        # Prepare updates dict for PackageManager
        updates = {}
        
        # Map frontend field names to package component keys
        if 'tpe' in package_components:
            updates['basic_salary'] = float(package_components['tpe'])
        if 'car_allowance' in package_components:
            updates['car_allowance'] = float(package_components['car_allowance'])
        if 'bonus' in package_components:
            updates['bonus'] = float(package_components['bonus'])
        if 'pension_option' in package_components:
            updates['pension_option'] = package_components['pension_option']
        if 'group_life_option' in package_components:
            updates['group_life_option'] = package_components['group_life_option']
        
        # Update package using PackageManager (with validation)
        result = package_manager.update_employee_package(employee_id, updates)
        
        if not result['success']:
            return jsonify({'success': False, 'error': result.get('error', 'Failed to update package')})
        
        # Create audit trail entry
        user_type = 'admin' if session.get('isRandWaterAdmin') else 'super_admin'
        user_id = session.get('username', 'admin')
        
        package_manager.add_audit_entry(
            employee_id=employee_id,
            action='package_updated',
            changes={'changes': change_summary},
            user_type=user_type,
            user_id=user_id
        )
        
        # Get updated package
        updated_package = package_manager.get_employee_package(employee_id)
        
        return jsonify({
            'success': True,
            'message': 'Package updated successfully',
            'package': updated_package,
            'current_tctc': updated_package.get('current_tctc', 0),
            'warnings': result.get('warnings', []),
            'percentages': result.get('percentages', {}),
            'remaining_budget': result.get('remaining_budget', 0)
        })
        
    except Exception as e:
        logger.error(f"Error updating package for {employee_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/package_edit_fullpage/<employee_id>')
def package_edit_fullpage(employee_id):
    """Full-page package edit interface"""
    if not session.get('admin') and not session.get('isRandWaterAdmin') and not session.get('isSuperAdmin'):
        return redirect(url_for('unified_login'))
    
    try:
        # Get employee package data
        package = package_manager.get_employee_package(employee_id)
        if not package:
            flash(f'Package not found for employee {employee_id}', 'error')
            return redirect(url_for('manage_packages'))
        
        # Get employee access info
        employee_access_info = employee_access.get_employee_by_id(employee_id)
        if not employee_access_info:
            flash(f'Employee access not found for {employee_id}', 'error')
            return redirect(url_for('manage_packages'))
        
        # Get SAP data for the employee
        sap_data = package_manager.get_sap_data_for_employee(employee_id)
        
        # Combine all employee data
        employee = {
            'employee_id': employee_id,
            'sap_data': sap_data or {},
            'package_components': package.get('package_components', {}),
            'tctc_limit': package.get('tctc_limit', 0),
            'current_tctc': package.get('current_tctc', 0)
        }
        
        # Debug logging
        print(f"DEBUG: Employee data being sent to template: {employee}")
        print(f"DEBUG: SAP data keys: {list(employee['sap_data'].keys()) if employee['sap_data'] else 'None'}")
        print(f"DEBUG: Package components keys: {list(employee['package_components'].keys()) if employee['package_components'] else 'None'}")
        
        return render_template('package_edit_fullpage.html', employee=employee)
        
    except Exception as e:
        logger.error(f"Error loading full-page edit for {employee_id}: {str(e)}")
        flash(f'Error loading package: {str(e)}', 'error')
        return redirect(url_for('manage_packages'))

@app.route('/package_edit/<employee_id>', methods=['POST'])
def package_edit(employee_id):
    """Edit/Update employee package"""
    if not session.get('admin') and not session.get('isRandWaterAdmin') and not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get form data
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        logger.info(f"Package edit data received for {employee_id}: {data}")
        
        # Get current package
        current_package = package_manager.get_employee_package(employee_id)
        if not current_package:
            return jsonify({'error': 'Package not found'}), 404
        
        # Update package components with new values
        package_components = current_package.get('package_components', {})
        
        # Track changes for audit trail
        changes = {}
        old_values = {}
        
        # Update individual components if provided
        if 'basic_salary' in data:
            old_values['basic_salary'] = package_components.get('basic_salary', 0)
            package_components['basic_salary'] = float(data['basic_salary'])
            changes['basic_salary'] = {'old': old_values['basic_salary'], 'new': float(data['basic_salary'])}
        if 'car_allowance' in data:
            old_values['car_allowance'] = package_components.get('car_allowance', 0)
            package_components['car_allowance'] = float(data['car_allowance'])
            changes['car_allowance'] = {'old': old_values['car_allowance'], 'new': float(data['car_allowance'])}
        if 'cellphone_allowance' in data:
            old_values['cellphone_allowance'] = package_components.get('cellphone_allowance', 0)
            package_components['cellphone_allowance'] = float(data['cellphone_allowance'])
            changes['cellphone_allowance'] = {'old': old_values['cellphone_allowance'], 'new': float(data['cellphone_allowance'])}
        if 'data_service_allowance' in data:
            old_values['data_service_allowance'] = package_components.get('data_service_allowance', 0)
            package_components['data_service_allowance'] = float(data['data_service_allowance'])
            changes['data_service_allowance'] = {'old': old_values['data_service_allowance'], 'new': float(data['data_service_allowance'])}
        if 'housing_allowance' in data:
            old_values['housing_allowance'] = package_components.get('housing_allowance', 0)
            package_components['housing_allowance'] = float(data['housing_allowance'])
            changes['housing_allowance'] = {'old': old_values['housing_allowance'], 'new': float(data['housing_allowance'])}
        if 'medical_aid' in data:
            old_values['medical_aid'] = package_components.get('medical_aid', 0)
            package_components['medical_aid'] = float(data['medical_aid'])
            changes['medical_aid'] = {'old': old_values['medical_aid'], 'new': float(data['medical_aid'])}
        if 'bonus' in data:
            old_values['bonus'] = package_components.get('bonus', 0)
            package_components['bonus'] = float(data['bonus'])
            changes['bonus'] = {'old': old_values['bonus'], 'new': float(data['bonus'])}
        if 'other_allowances' in data:
            old_values['other_allowances'] = package_components.get('other_allowances', 0)
            package_components['other_allowances'] = float(data['other_allowances'])
            changes['other_allowances'] = {'old': old_values['other_allowances'], 'new': float(data['other_allowances'])}
        
        # Calculate new TCTC
        new_tctc = sum([
            package_components.get('basic_salary', 0),
            package_components.get('car_allowance', 0),
            package_components.get('cellphone_allowance', 0),
            package_components.get('data_service_allowance', 0),
            package_components.get('housing_allowance', 0),
            package_components.get('medical_aid', 0),
            package_components.get('bonus', 0),
            package_components.get('other_allowances', 0)
        ])
        
        # Update package
        current_package['package_components'] = package_components
        current_package['current_tctc'] = new_tctc
        current_package['last_modified'] = datetime.now().isoformat()
        
        # Save updated package (in a real app, this would save to database)
        success = package_manager.update_employee_package(employee_id, current_package)
        
        if success:
            # Add audit trail entry for the changes
            if changes:
                user_type = 'admin' if session.get('isRandWaterAdmin') else 'super_admin'
                user_id = session.get('username', 'admin')
                logger.info(f"Creating audit trail entry for {employee_id}: changes={changes}, user_type={user_type}, user_id={user_id}")
                package_manager.add_audit_entry(
                    employee_id=employee_id,
                    action='package_updated',
                    changes=changes,
                    user_type=user_type,
                    user_id=user_id
                )
                logger.info(f"Audit trail entry created successfully")
            
            logger.info(f"Package updated successfully for {employee_id}, new TCTC: {new_tctc}")
            
            return jsonify({
                'success': True,
                'message': f'Package updated successfully for {employee_id}',
                'new_tctc': new_tctc
            })
        else:
            return jsonify({'error': 'Failed to save package'}), 500
        
    except Exception as e:
        logger.error(f"Error updating package for {employee_id}: {str(e)}")
        return jsonify({'error': f'Error updating package: {str(e)}'}), 500

@app.route('/admin/randwater/employee-payslip/<employee_id>')
def employee_payslip(employee_id):
    """Rand Water Admin - Get employee payslip data from uploaded SAP file"""
    if not session.get('admin') and not session.get('isRandWaterAdmin') and not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401

    def safe_float(value, default=0.0):
        """Safely convert value to float, handling text values like 'Yes', 'No'"""
        if value is None:
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
        # Get employee package data
        package = package_manager.get_employee_package(employee_id)
        if not package:
            return jsonify({'error': f'Employee {employee_id} package not found'}), 404
        
        # Get SAP data for the employee
        sap_data = package_manager.get_sap_data_for_employee(employee_id)
        if not sap_data:
            return jsonify({'error': f'Employee {employee_id} SAP data not found'}), 404
        
        # Extract payslip data with safety checks
        package_components = package.get('package_components', {})
        if not package_components:
            package_components = {}
            
        payslip_data = {
            'success': True,
            'employee': {
                'employee_id': str(sap_data.get('EMPLOYEECODE', employee_id)),
                'first_name': str(sap_data.get('FIRSTNAME', '')),
                'surname': str(sap_data.get('SURNAME', '')),
                'grade_band': str(sap_data.get('BAND', 'O-Q')),
                'department': str(sap_data.get('DEPARTMENT', 'General')),
                'job_title': str(sap_data.get('JOBLONG', 'Employee')),
                'basic_salary': safe_float(sap_data.get('TPE', 0)),
                'ctc': safe_float(sap_data.get('CTC', 0))
            },
            'payslip': {
                'basic_salary': safe_float(package_components.get('basic_salary', 0)),
                'car_allowance': safe_float(package_components.get('car_allowance', 0)),
                'cellphone_allowance': safe_float(package_components.get('cellphone_allowance', 0)),
                'data_service_allowance': safe_float(package_components.get('data_service_allowance', 0)),
                'housing_allowance': safe_float(package_components.get('housing_allowance', 0)),
                'provident_fund': safe_float(package_components.get('provident_fund', 0)),
                'medical_aid': safe_float(package_components.get('medical_aid', 0)),
                'bonus': safe_float(package_components.get('bonus', 0)),
                'current_tctc': safe_float(package.get('current_tctc', 0)),
                'tctc_limit': safe_float(package.get('tctc_limit', 0))
            }
        }
        
        # Calculate bonus provision (monthly amount deducted from package)
        bonus_provision_monthly = payslip_data['payslip']['bonus'] / 12 if payslip_data['payslip']['bonus'] > 0 else 0
        
        # Calculate total monthly earnings
        total_monthly = (payslip_data['payslip']['basic_salary'] + 
                        payslip_data['payslip']['car_allowance'] + 
                        payslip_data['payslip']['cellphone_allowance'] + 
                        payslip_data['payslip']['data_service_allowance'] + 
                        payslip_data['payslip']['housing_allowance'] + 
                        payslip_data['payslip']['medical_aid'] + 
                        bonus_provision_monthly)
        
        # Calculate net pay (basic salary - deductions)
        net_pay = payslip_data['payslip']['basic_salary'] - payslip_data['payslip']['provident_fund']
        
        payslip_data['payslip']['bonus_provision_monthly'] = bonus_provision_monthly
        payslip_data['payslip']['total_monthly_earnings'] = total_monthly
        payslip_data['payslip']['net_pay'] = net_pay
        
        return jsonify(payslip_data)
        
    except Exception as e:
        logger.error(f"Error getting employee payslip for {employee_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# SMTP CONFIGURATION FUNCTIONS
# ============================================================================

def load_smtp_settings():
    """Load SMTP settings from file"""
    smtp_file = 'smtp_settings.json'
    try:
        if os.path.exists(smtp_file):
            with open(smtp_file, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error loading SMTP settings: {e}")
        return None

def save_smtp_settings(settings):
    """Save SMTP settings to file"""
    smtp_file = 'smtp_settings.json'
    try:
        with open(smtp_file, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving SMTP settings: {e}")
        return False

# ===== SYSTEM SECURITY FUNCTIONS =====
def load_security_settings():
    """Load system security settings from file"""
    security_file = 'security_settings.json'
    try:
        if os.path.exists(security_file):
            with open(security_file, 'r') as f:
                return json.load(f)
        # Return default settings
        return {
            'password_policy': {
                'min_length': 8,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_numbers': True,
                'require_special': True,
                'max_age_days': 90
            },
            'session_policy': {
                'timeout_minutes': 30,
                'max_concurrent_sessions': 3,
                'require_2fa': False
            },
            'access_policy': {
                'max_login_attempts': 5,
                'lockout_duration_minutes': 15,
                'audit_logging': True
            }
        }
    except Exception as e:
        logger.error(f"Error loading security settings: {e}")
        return None

def save_security_settings(settings):
    """Save system security settings to file"""
    security_file = 'security_settings.json'
    try:
        with open(security_file, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving security settings: {e}")
        return False

# ===== SYSTEM BACKUP FUNCTIONS =====
def create_system_backup():
    """Create a complete system backup"""
    try:
        # Ensure backups directory exists
        if not os.path.exists('backups'):
            os.makedirs('backups')
            
        backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_data = {
            'timestamp': backup_timestamp,
            'created_date': datetime.now().isoformat(),
            'employee_access': employee_access.get_all_employees(),
            'employee_packages': package_manager.get_all_packages(),
            'smtp_settings': load_smtp_settings(),
            'security_settings': load_security_settings()
        }
        
        backup_filename = f'system_backup_{backup_timestamp}.json'
        backup_path = os.path.join('backups', backup_filename)
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        logger.info(f"System backup created: {backup_filename}")
        return backup_filename
    except Exception as e:
        logger.error(f"Error creating system backup: {e}")
        return None

def get_backup_list():
    """Get list of available system backups"""
    try:
        backups = []
        if os.path.exists('backups'):
            for filename in os.listdir('backups'):
                if filename.startswith('system_backup_') and filename.endswith('.json'):
                    filepath = os.path.join('backups', filename)
                    stat = os.stat(filepath)
                    backups.append({
                        'filename': filename,
                        'size': round(stat.st_size / 1024, 2),  # Size in KB
                        'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                    })
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    except Exception as e:
        logger.error(f"Error getting backup list: {e}")
        return []

def restore_system_backup(backup_filename):
    """Restore system from backup file"""
    try:
        backup_path = os.path.join('backups', backup_filename)
        if not os.path.exists(backup_path):
            return False, "Backup file not found"
            
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        # Restore employee access data
        with open('employee_access.json', 'w') as f:
            json.dump(backup_data.get('employee_access', []), f, indent=2)
            
        # Restore employee packages data
        with open('employee_packages.json', 'w') as f:
            json.dump(backup_data.get('employee_packages', []), f, indent=2)
            
        # Restore SMTP settings
        if backup_data.get('smtp_settings'):
            save_smtp_settings(backup_data['smtp_settings'])
            
        # Restore security settings
        if backup_data.get('security_settings'):
            save_security_settings(backup_data['security_settings'])
        
        logger.info(f"System restored from backup: {backup_filename}")
        return True, "System successfully restored"
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return False, f"Error restoring backup: {str(e)}"

# ===== SYSTEM ANALYTICS FUNCTIONS =====
def get_system_analytics():
    """Calculate and return system analytics data"""
    try:
        # Get current data
        all_employees = employee_access.get_all_employees()
        all_packages = package_manager.get_all_packages()
        
        # Calculate analytics
        analytics = {
            'user_stats': {
                'total_users': len(all_employees),
                'active_packages': len(all_packages),
                'completion_rate': round((len(all_packages) / max(len(all_employees), 1)) * 100, 1) if all_employees else 0
            },
            'system_stats': {
                'uptime_days': 30,  # This would be calculated from actual system start time
                'total_logins_today': len(all_employees) * 2,  # Simulated data
                'avg_session_duration': 25,  # minutes - simulated
                'peak_usage_hour': '14:00',
                'server_status': 'Running',
                'last_backup': get_last_backup_date()
            },
            'package_stats': calculate_package_statistics(all_packages),
            'monthly_trends': get_monthly_trends()
        }
        return analytics
    except Exception as e:
        logger.error(f"Error calculating analytics: {e}")
        return {
            'user_stats': {'total_users': 0, 'active_packages': 0, 'completion_rate': 0},
            'system_stats': {'uptime_days': 0, 'total_logins_today': 0, 'avg_session_duration': 0, 'peak_usage_hour': '00:00', 'server_status': 'Unknown', 'last_backup': 'Never'},
            'package_stats': {'total_packages': 0, 'avg_tctc': 0, 'highest_tctc': 0, 'lowest_tctc': 0},
            'monthly_trends': []
        }

def calculate_package_statistics(packages):
    """Calculate package-related statistics"""
    if not packages:
        return {
            'total_packages': 0,
            'avg_tctc': 0,
            'highest_tctc': 0,
            'lowest_tctc': 0,
            'avg_deductions': 0,
            'most_common_benefits': []
        }
    
    tctc_values = [float(p.get('tctc', 0)) for p in packages if p.get('tctc')]
    
    return {
        'total_packages': len(packages),
        'avg_tctc': round(sum(tctc_values) / len(tctc_values), 2) if tctc_values else 0,
        'highest_tctc': max(tctc_values) if tctc_values else 0,
        'lowest_tctc': min(tctc_values) if tctc_values else 0,
        'avg_deductions': round(sum([float(p.get('total_deductions', 0)) for p in packages]) / len(packages), 2),
        'most_common_benefits': ['Medical Aid', 'Provident Fund', 'Car Allowance']  # This would be calculated from actual data
    }

def get_last_backup_date():
    """Get the date of the most recent backup"""
    try:
        backups = get_backup_list()
        return backups[0]['created'] if backups else 'Never'
    except:
        return 'Never'

def get_monthly_trends():
    """Get monthly usage trends (simulated data for now)"""
    return [
        {'month': 'Jan', 'users': 45, 'packages': 42},
        {'month': 'Feb', 'users': 48, 'packages': 46},
        {'month': 'Mar', 'users': 52, 'packages': 49},
        {'month': 'Apr', 'users': 55, 'packages': 52},
        {'month': 'May', 'users': 58, 'packages': 55},
        {'month': 'Jun', 'users': 62, 'packages': 59}
    ]

@app.route('/api/smtp/test', methods=['POST'])
def test_smtp_connection_superadmin():
    """Test SMTP connection and send test email"""
    if not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        # Extract SMTP settings
        host = data.get('smtp_host')
        port = int(data.get('smtp_port', 587))
        username = data.get('smtp_username')
        password = data.get('smtp_password')
        security = data.get('smtp_security', 'tls')
        from_name = data.get('smtp_from_name', 'Rand Water SmartHR')
        
        if not all([host, username, password]):
            return jsonify({'error': 'Missing required SMTP settings'}), 400
        
        # Create test email
        msg = MIMEMultipart()
        msg['From'] = f"{from_name} <{username}>"
        msg['To'] = username
        msg['Subject'] = "SMTP Test - Rand Water SmartHR"
        
        body = f"""
        SMTP Configuration Test Successful!
        
        This is a test email to verify your SMTP configuration for Rand Water SmartHR.
        
        Configuration Details:
        - SMTP Host: {host}
        - Port: {port}
        - Security: {security.upper()}
        - From: {from_name}
        
        If you received this email, your SMTP configuration is working correctly.
        
        Best regards,
        Rand Water SmartHR System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect and send
        if security == 'ssl':
            server = smtplib.SMTP_SSL(host, port)
        else:
            server = smtplib.SMTP(host, port)
            if security == 'tls':
                server.starttls()
        
        server.login(username, password)
        server.send_message(msg)
        server.quit()
        
        return jsonify({'success': True, 'message': 'Test email sent successfully'})
        
    except Exception as e:
        logger.error(f"SMTP test failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/smtp/save', methods=['POST'])
def save_smtp_config():
    """Save SMTP configuration"""
    if not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['smtp_host', 'smtp_port', 'smtp_username', 'smtp_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Prepare settings
        smtp_settings = {
            'host': data.get('smtp_host'),
            'port': int(data.get('smtp_port')),
            'username': data.get('smtp_username'),
            'password': data.get('smtp_password'),  # In production, encrypt this
            'security': data.get('smtp_security', 'tls'),
            'from_name': data.get('smtp_from_name', 'Rand Water SmartHR'),
            'enable_notifications': data.get('enable_notifications', False),
            'enable_reports': data.get('enable_reports', False),
            'enable_alerts': data.get('enable_alerts', False),
            'updated_date': datetime.now().isoformat(),
            'updated_by': session.get('superadmin_username', 'Unknown')
        }
        
        # Save settings
        if save_smtp_settings(smtp_settings):
            return jsonify({'success': True, 'message': 'SMTP settings saved successfully'})
        else:
            return jsonify({'error': 'Failed to save SMTP settings'}), 500
            
    except Exception as e:
        logger.error(f"Error saving SMTP settings: {e}")
        return jsonify({'error': str(e)}), 500

# ===== SYSTEM SECURITY API ROUTES =====
@app.route('/api/security/save', methods=['POST'])
def save_security_config():
    """Save system security configuration"""
    if not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        # Save security settings
        if save_security_settings(data):
            return jsonify({'success': True, 'message': 'Security settings saved successfully'})
        else:
            return jsonify({'error': 'Failed to save security settings'}), 500
            
    except Exception as e:
        logger.error(f"Error saving security settings: {e}")
        return jsonify({'error': str(e)}), 500

# ===== PENSION & GROUP LIFE CONFIG API ROUTES =====
@app.route('/api/pension-config/get', methods=['GET'])
def get_pension_config():
    """Get pension and group life configuration"""
    if not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        with open('pension_config.json', 'r') as f:
            config = json.load(f)
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        logger.error(f"Error loading pension config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pension-config/save', methods=['POST'])
def save_pension_config():
    """Save pension and group life configuration"""
    if not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        # Update last_updated timestamp
        data['last_updated'] = datetime.now().isoformat()
        data['updated_by'] = session.get('username', 'superadmin')
        
        # Save to file
        with open('pension_config.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Pension config updated by {data['updated_by']}")
        return jsonify({'success': True, 'message': 'Configuration saved successfully'})
        
    except Exception as e:
        logger.error(f"Error saving pension config: {e}")
        return jsonify({'error': str(e)}), 500

# ===== SYSTEM BACKUP API ROUTES =====
@app.route('/api/backup/create', methods=['POST'])
def create_backup():
    """Create a new system backup"""
    if not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        backup_filename = create_system_backup()
        if backup_filename:
            return jsonify({'success': True, 'filename': backup_filename, 'message': 'Backup created successfully'})
        else:
            return jsonify({'error': 'Failed to create backup'}), 500
            
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/restore', methods=['POST'])
def restore_backup():
    """Restore system from backup"""
    if not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        backup_filename = data.get('filename')
        
        if not backup_filename:
            return jsonify({'error': 'Backup filename required'}), 400
            
        success, message = restore_system_backup(backup_filename)
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'error': message}), 500
            
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/download/<filename>')
def download_backup(filename):
    """Download a backup file"""
    if not session.get('isSuperAdmin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        backup_path = os.path.join('backups', filename)
        if os.path.exists(backup_path):
            return send_file(backup_path, as_attachment=True)
        else:
            return jsonify({'error': 'Backup file not found'}), 404
            
    except Exception as e:
        logger.error(f"Error downloading backup: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001)
