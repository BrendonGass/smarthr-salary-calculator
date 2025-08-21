from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, g
import json
import math
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sap_integration import SAPIntegration, SAP_CONFIG
import os
from datetime import datetime
import logging
import requests

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Change this in production

SETTINGS_FILE = 'tax_settings.json'

# Initialize SAP integration
sap_integration = SAPIntegration(SAP_CONFIG)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load tax configuration
def load_tax_settings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
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

@app.before_request
def before_request():
    """Handle SSO token and user authentication"""
    # Check for SSO token in request
    sso_token = request.args.get('sso_token') or request.headers.get('X-SSO-Token')
    user_id = request.args.get('user_id') or request.headers.get('X-User-ID')
    
    if sso_token and user_id:
        # Validate SSO token with your ESS system
        if validate_sso_token(sso_token, user_id):
            session['user_id'] = user_id
            session['authenticated'] = True
            g.current_user = user_id
        else:
            return jsonify({'error': 'Invalid SSO token'}), 401

def validate_sso_token(token, user_id):
    """Validate SSO token with ESS system"""
    # Implement your SSO validation logic here
    # This should communicate with your ESS authentication system
    try:
        # Example validation - replace with your actual SSO validation
        response = requests.post(
            'https://your-ess-system.com/validate-token',
            json={'token': token, 'user_id': user_id},
            timeout=5
        )
        return response.status_code == 200
    except:
        # For development, accept any token
        return True

@app.route('/')
def index():
    """Main entry point - redirects to iframe-friendly calculator"""
    return redirect(url_for('calculator_iframe'))

@app.route('/calculator/iframe')
def calculator_iframe():
    """iFrame-friendly calculator view"""
    return render_template('calculator_iframe.html')

@app.route('/api/employee/<employee_id>')
def get_employee_data(employee_id):
    """API endpoint to get employee data from SAP"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get employee data from SAP
        employee_data = sap_integration.get_employee_data(employee_id)
        salary_data = sap_integration.get_salary_data(employee_id)
        
        if not employee_data:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Combine employee and salary data
        combined_data = {**employee_data, **salary_data}
        
        return jsonify(combined_data)
        
    except Exception as e:
        logger.error(f"Error fetching employee data: {str(e)}")
        return jsonify({'error': 'Failed to fetch employee data'}), 500

@app.route('/api/package/submit', methods=['POST'])
def submit_package():
    """Submit employee package changes to SAP"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        package_data = data.get('package_data')
        
        if not employee_id or not package_data:
            return jsonify({'error': 'Missing required data'}), 400
        
        # Submit to SAP
        success = sap_integration.submit_package_changes(employee_id, package_data)
        
        if success:
            # Save to local storage for tracking
            save_completed_package(employee_id, package_data)
            return jsonify({'message': 'Package submitted successfully'})
        else:
            return jsonify({'error': 'Failed to submit package'}), 500
            
    except Exception as e:
        logger.error(f"Error submitting package: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/packages/export')
def export_completed_packages():
    """Export all completed packages for SAP upload"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get all completed packages
        completed_packages = get_all_completed_packages()
        
        if not completed_packages:
            return jsonify({'error': 'No completed packages found'}), 404
        
        # Generate SAP export file
        export_file = sap_integration.generate_sap_export_file(completed_packages)
        
        if export_file:
            return send_file(
                export_file,
                as_attachment=True,
                download_name=f"sap_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
        else:
            return jsonify({'error': 'Failed to generate export file'}), 500
            
    except Exception as e:
        logger.error(f"Error exporting packages: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/packages/status')
def get_packages_status():
    """Get status of all packages (for admin dashboard)"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get package statistics
        stats = get_package_statistics()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting package status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/calculator/<mode>')
def calculator_mode(mode):
    """Calculator with different modes"""
    if mode == 'basic':
        return render_template('basic_form_enhanced.html')
    elif mode == 'ctc':
        return render_template('ctc_form_enhanced.html')
    elif mode == 'netpay':
        return render_template('netpay_form_enhanced.html')
    else:
        return redirect(url_for('calculator_mode', mode='basic'))

@app.route('/calculate', methods=['POST'])
def calculate():
    """Enhanced calculation endpoint with SAP data integration"""
    try:
        form = request.form
        mode = form.get("mode", "basic")
        settings = load_tax_settings()

        # Parse all earnings, deductions, employer contributions
        earnings = parse_group(form, prefix="earnings")
        deductions = parse_group(form, prefix="deductions")
        employer = parse_group(form, prefix="employer")

        gross = sum(val for label, val in earnings)
        total_deductions = sum(val for label, val in deductions)
        total_employer = sum(val for label, val in employer)

        # SARS-compliant UIF calculation
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
            "uif": round(uif, 2),
            "monthly_tax": monthly_tax,
            "take_home": round(net_pay, 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

def parse_group(form, prefix):
    """Parse form groups (earnings, deductions, employer)"""
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

def save_completed_package(employee_id, package_data):
    """Save completed package to local storage"""
    try:
        completed_packages_file = 'completed_packages.json'
        
        # Load existing packages
        if os.path.exists(completed_packages_file):
            with open(completed_packages_file, 'r') as f:
                packages = json.load(f)
        else:
            packages = []
        
        # Add new package
        package_record = {
            'employee_id': employee_id,
            'package_data': package_data,
            'submission_date': datetime.now().isoformat(),
            'status': 'COMPLETED'
        }
        
        packages.append(package_record)
        
        # Save back to file
        with open(completed_packages_file, 'w') as f:
            json.dump(packages, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error saving completed package: {str(e)}")

def get_all_completed_packages():
    """Get all completed packages"""
    try:
        completed_packages_file = 'completed_packages.json'
        
        if os.path.exists(completed_packages_file):
            with open(completed_packages_file, 'r') as f:
                return json.load(f)
        else:
            return []
            
    except Exception as e:
        logger.error(f"Error loading completed packages: {str(e)}")
        return []

def get_package_statistics():
    """Get package submission statistics"""
    try:
        packages = get_all_completed_packages()
        
        total_packages = len(packages)
        completed_packages = len([p for p in packages if p.get('status') == 'COMPLETED'])
        pending_packages = total_packages - completed_packages
        
        return {
            'total_packages': total_packages,
            'completed_packages': completed_packages,
            'pending_packages': pending_packages,
            'completion_rate': (completed_packages / total_packages * 100) if total_packages > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting package statistics: {str(e)}")
        return {}

# Admin routes (enhanced)
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if session.get('isSuperUser'):
        return redirect(url_for('admin_panel'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'SuperUser' and password == '$m@rtHR7!':
            session['admin'] = True
            session['isSuperUser'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = "Incorrect username or password"
    return render_template('admin_login.html', error=error)

@app.route('/admin/dashboard')
def admin_panel():
    if not session.get('admin') and not session.get('isSuperUser'):
        return redirect(url_for('admin_login'))
    
    settings = load_tax_settings()
    stats = get_package_statistics()
    
    return render_template('admin_panel_enhanced.html', settings=settings, stats=stats)

@app.route('/admin/update', methods=['POST'])
def update_settings():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    settings = {
        "rebate_primary": float(request.form.get("rebate_primary", 17235)),
        "rebate_secondary": float(request.form.get("rebate_secondary", 9444)),
        "rebate_tertiary": float(request.form.get("rebate_tertiary", 3145)),
        "uif_ceiling": float(request.form.get("uif_ceiling", 177.12)),
        "medical_main": float(request.form.get("medical_main", 364)),
        "medical_first": float(request.form.get("medical_first", 364)),
        "medical_additional": float(request.form.get("medical_additional", 246)),
    }
    
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

    return render_template('admin_panel_enhanced.html', settings=settings, message='Settings updated successfully!')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 