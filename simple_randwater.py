from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'randwater-super-secret-key-2024'

# Rand Water specific configuration
RANDWATER_CONFIG = {
    'company_name': 'Rand Water',
    'company_logo': '/static/images/randwater-logo.png',
    'brand_colors': {
        'primary': '#0066CC',
        'secondary': '#00A3E0',
        'accent': '#FF6600'
    }
}

# ============================================================================
# UNIFIED LOGIN SYSTEM
# ============================================================================

@app.route('/')
def index():
    """Main entry point - unified login screen"""
    return render_template('login.html', config=RANDWATER_CONFIG)

@app.route('/login', methods=['GET', 'POST'])
def unified_login():
    """Unified login that routes to different dashboards based on credentials"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check for Super Admin
        if username == 'SuperAdmin' and password == 'SmartHR2024!SuperAdmin':
            session['isSuperAdmin'] = True
            session['superadmin_username'] = username
            return redirect(url_for('super_admin_dashboard'))
        
        # Check for Randwater Admin
        elif username == 'RandWaterAdmin' and password == 'RandWater2024!':
            session['admin'] = True
            session['isRandWaterAdmin'] = True
            return redirect(url_for('randwater_admin_panel'))
        
        # Check for Employee
        else:
            # Simple employee validation (you can enhance this)
            if username.startswith('RW') and len(username) >= 6:
                session['employee_id'] = username
                session['username'] = username
                return redirect(url_for('employee_dashboard'))
            else:
                return render_template('login.html', error="Invalid credentials", config=RANDWATER_CONFIG)
    
    return render_template('login.html', config=RANDWATER_CONFIG)

@app.route('/logout')
def unified_logout():
    """Unified logout"""
    session.clear()
    return redirect(url_for('unified_login'))

# ============================================================================
# EMPLOYEE ROUTES
# ============================================================================

@app.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    """Employee login (redirects to unified login)"""
    return redirect(url_for('unified_login'))

@app.route('/employee/logout')
def employee_logout():
    """Employee logout (redirects to unified logout)"""
    return redirect(url_for('unified_logout'))

@app.route('/employee/dashboard')
def employee_dashboard():
    """Employee dashboard"""
    if not session.get('employee_id'):
        return redirect(url_for('unified_login'))
    
    return render_template('employee_login.html', 
                         employee_id=session.get('employee_id'),
                         config=RANDWATER_CONFIG)

# ============================================================================
# SUPER ADMIN ROUTES
# ============================================================================

@app.route('/superadmin/login', methods=['GET', 'POST'])
def super_admin_login():
    """Super Admin login (redirects to unified login)"""
    return redirect(url_for('unified_login'))

@app.route('/superadmin/logout')
def super_admin_logout():
    """Super Admin logout (redirects to unified logout)"""
    return redirect(url_for('unified_logout'))

@app.route('/superadmin/dashboard')
def super_admin_dashboard():
    """Super Admin dashboard"""
    if not session.get('isSuperAdmin'):
        return redirect(url_for('unified_login'))
    
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
    """Randwater admin login (redirects to unified login if not authenticated)"""
    if session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_panel'))
    
    # If not authenticated, redirect to unified login
    return redirect(url_for('unified_login'))

@app.route('/admin/randwater/dashboard')
def randwater_admin_panel():
    """Randwater admin dashboard"""
    if not session.get('admin') and not session.get('isRandWaterAdmin'):
        return redirect(url_for('randwater_admin_login'))
    
    stats = {
        'total_packages': 25,  # Placeholder
        'completed_packages': 20,  # Placeholder
        'company': 'RANDWATER'
    }
    
    return render_template('randwater_admin_panel.html', 
                         settings={}, 
                         stats=stats, 
                         config=RANDWATER_CONFIG)

# ============================================================================
# CALCULATOR ROUTES
# ============================================================================

@app.route('/calculator')
def calculator():
    """Main calculator view"""
    return render_template('randwater_calculator.html', config=RANDWATER_CONFIG)

@app.route('/calculate', methods=['POST'])
def calculate():
    """Basic salary calculation"""
    try:
        data = request.get_json()
        basic_salary = float(data.get('basic_salary', 0))
        
        # Simple calculation
        gross = basic_salary
        tax = gross * 0.18  # Simplified tax
        net = gross - tax
        
        return jsonify({
            'gross': gross,
            'tax': round(tax, 2),
            'net': round(net, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    print("Starting Simple Randwater Calculator...")
    print("Available routes:")
    print("  - Main Login: http://localhost:5001/")
    print("  - Employee Login: http://localhost:5001/employee/login")
    print("  - Super Admin: http://localhost:5001/superadmin/login")
    print("  - Randwater Admin: http://localhost:5001/admin/randwater")
    print("  - Calculator: http://localhost:5001/calculator")
    print("\nPress Ctrl+C to stop")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
