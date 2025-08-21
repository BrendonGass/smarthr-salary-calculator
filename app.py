from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session 
import json
import math
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Change this in production

SETTINGS_FILE = 'tax_settings.json'

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

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    # Clear session data
    session.clear()
    # Return a page that clears sessionStorage and redirects to login
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logging out...</title>
    </head>
    <body>
        <script>
            // Clear sessionStorage
            sessionStorage.clear();
            // Redirect to login page
            window.location.href = '/';
        </script>
        <p>Logging out...</p>
    </body>
    </html>
    '''

@app.route('/basic')
def basic_salary_view():
    return render_template('basic_form.html')

@app.route('/ctc')
def ctc_view():
    return render_template('ctc_form.html')

@app.route('/netpay')
def netpay_view():
    return render_template('netpay_form.html')

@app.route('/calculator/<mode>')
def calculator_mode(mode):
    if mode == 'basic':
        return render_template('basic_form.html')
    elif mode == 'ctc':
        return render_template('ctc_form.html')
    elif mode == 'netpay':
        return render_template('netpay_form.html')
    else:
        return redirect(url_for('basic_salary_view'))

@app.route('/calculate', methods=['POST'])
def calculate():
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
        uif_cap = settings.get('uif_ceiling', 17712)  # Monthly UIF cap from admin dashboard
        uif = min(uif_cap, gross * 0.01)
        
        # Get age and medical info
        age = int(form.get("age", 0))
        has_medical = form.get("has_medical", "no") == "yes"
        dependants = int(form.get("dependants", 0))

        # Calculate taxable income (including travel allowance)
        travel_allowance = next((val for label, val in earnings if 'transport' in label.lower()), 0)
        annual_travel_taxable = travel_allowance * 12 * 0.8
        # Remove travel allowance from gross for tax calculation, then add 80% back
        gross_excluding_travel = gross - travel_allowance
        taxable_income = gross_excluding_travel * 12 + annual_travel_taxable

        # Calculate pension deductions
        pension_employee = next((val for label, val in deductions if 'pension' in label.lower()), 0)
        pension_employer = next((val for label, val in employer if 'pension' in label.lower()), 0)
        
        # Total pension deductible (capped at 27.5% of taxable income or R350,000)
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
    # Try to get tax brackets from admin dashboard
    try:
        import json
        tax_brackets = json.loads(settings.get('tax_brackets', '[]'))
        
        if tax_brackets:
            # Use admin dashboard brackets
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

# Calculate age from ID number
def calculate_age_from_id(id_number):
    if len(id_number) >= 6:
        year = int(id_number[:2])
        month = int(id_number[2:4])
        day = int(id_number[4:6])
        
        # Determine century (assuming 1900s for years 00-29, 2000s for 30-99)
        full_year = 2000 + year if year <= 29 else 1900 + year
        
        from datetime import datetime, date
        birth_date = date(full_year, month, day)
        today = date.today()
        age = today.year - birth_date.year
        
        # Adjust age if birthday hasn't occurred this year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
            
        return age
    return 0

# ---------------- Admin Routes ------------------
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    # Check if user is super user from session
    if session.get('isSuperUser'):
        return redirect(url_for('admin_panel'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Super user authentication
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
    return render_template('admin_panel.html', settings=settings)

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

    return render_template('admin_panel.html', settings=settings, message='Settings updated successfully!')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    