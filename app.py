from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        gross_salary = float(request.form.get("salary", 0))
        travel = float(request.form.get("travel", 0))
        travel_included = request.form.get("travel_included", "yes") == "yes"
        pension_type = request.form.get("pension_type", "value")
        pension_employee_input = float(request.form.get("pension_employee_input", 0))
        pension_employer = float(request.form.get("pension_employer", 0))
        pensionable_percent = float(request.form.get("pensionable_percent", 100))
        age = int(request.form.get("age", 0))
        has_medical = request.form.get("has_medical", "no") == "yes"
        dependants = int(request.form.get("dependants", 0))
    except ValueError:
        return jsonify({"error": "Invalid input. Please make sure all values are correctly filled."}), 400

    # Handle travel allowance
    monthly_salary = gross_salary
    if travel_included:
        monthly_salary -= travel

    annual_income = monthly_salary * 12
    annual_travel_taxable = travel * 12 * 0.8
    taxable_income = annual_income + annual_travel_taxable

    # Pension calculation
    pensionable_income = monthly_salary * (pensionable_percent / 100)
    pension_employee = pension_employee_input if pension_type == "value" else pensionable_income * (pension_employee_input / 100)
    annual_pension_employee = pension_employee * 12
    annual_pension_employer = pension_employer * 12
    total_pension_deductible = annual_pension_employee + annual_pension_employer
    total_pension_deductible = min(total_pension_deductible, 0.275 * taxable_income, 350000)

    taxable_income -= total_pension_deductible

    def calculate_tax(income):
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

    annual_tax = calculate_tax(taxable_income)

    # Apply age rebates
    rebate = 17235
    if age >= 65:
        rebate += 9444
    if age >= 75:
        rebate += 3145
    annual_tax -= rebate
    annual_tax = max(0, annual_tax)

    # Medical credits
    if has_medical:
        monthly_medical_credit = 364
        if dependants >= 1:
            monthly_medical_credit += 364
            if dependants > 1:
                monthly_medical_credit += (dependants - 1) * 246
        annual_tax -= monthly_medical_credit * 12

    annual_tax = max(0, annual_tax)
    monthly_tax = round(annual_tax / 12, 2)

    # UIF
    uif = min(177.12, monthly_salary * 0.01)

    # Final take-home pay
    take_home = gross_salary - monthly_tax - uif - pension_employee

    results = {
        "name": name,
        "email": email,
        "gross": round(gross_salary, 2),
        "travel": round(travel, 2),
        "monthly_tax": monthly_tax,
        "uif": round(uif, 2),
        "pension_employee": round(pension_employee, 2),
        "take_home": round(take_home, 2)
    }

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
