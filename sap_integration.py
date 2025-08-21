import requests
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional
import logging

class SAPIntegration:
    """
    SAP Integration module for the salary calculator
    Handles data exchange between SAP and the calculator
    """
    
    def __init__(self, sap_config: Dict):
        self.sap_base_url = sap_config.get('base_url')
        self.sap_username = sap_config.get('username')
        self.sap_password = sap_config.get('password')
        self.sap_client = sap_config.get('client')
        self.logger = logging.getLogger(__name__)
        
    def get_employee_data(self, employee_id: str) -> Dict:
        """
        Fetch employee data from SAP
        Returns: Employee personal and financial data
        """
        try:
            # SAP RFC call to get employee master data
            endpoint = f"{self.sap_base_url}/sap/opu/odata/sap/ZHR_EMPLOYEE_SRV/EmployeeSet('{employee_id}')"
            
            headers = {
                'Authorization': f'Basic {self._get_auth_token()}',
                'Accept': 'application/json'
            }
            
            response = requests.get(endpoint, headers=headers, timeout=30)
            response.raise_for_status()
            
            employee_data = response.json()
            
            # Transform SAP data to calculator format
            return self._transform_employee_data(employee_data)
            
        except Exception as e:
            self.logger.error(f"Error fetching employee data: {str(e)}")
            return {}
    
    def get_salary_data(self, employee_id: str) -> Dict:
        """
        Fetch current salary and benefits data from SAP
        Returns: Current CTC, allowances, deductions
        """
        try:
            # SAP RFC call to get salary information
            endpoint = f"{self.sap_base_url}/sap/opu/odata/sap/ZHR_SALARY_SRV/SalarySet"
            params = {
                '$filter': f"EmployeeId eq '{employee_id}'",
                '$select': 'BasicSalary,Allowances,Deductions,EmployerContributions'
            }
            
            headers = {
                'Authorization': f'Basic {self._get_auth_token()}',
                'Accept': 'application/json'
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            salary_data = response.json()
            
            return self._transform_salary_data(salary_data)
            
        except Exception as e:
            self.logger.error(f"Error fetching salary data: {str(e)}")
            return {}
    
    def submit_package_changes(self, employee_id: str, package_data: Dict) -> bool:
        """
        Submit employee package changes back to SAP
        Returns: Success status
        """
        try:
            # Transform calculator data to SAP format
            sap_data = self._transform_to_sap_format(package_data)
            
            # SAP RFC call to update employee package
            endpoint = f"{self.sap_base_url}/sap/opu/odata/sap/ZHR_PACKAGE_SRV/PackageSet"
            
            headers = {
                'Authorization': f'Basic {self._get_auth_token()}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            payload = {
                'EmployeeId': employee_id,
                'PackageData': sap_data,
                'SubmissionDate': datetime.now().isoformat(),
                'Status': 'SUBMITTED'
            }
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            self.logger.info(f"Package changes submitted successfully for employee {employee_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error submitting package changes: {str(e)}")
            return False
    
    def generate_sap_export_file(self, completed_packages: List[Dict]) -> str:
        """
        Generate SAP-compatible export file for completed packages
        Returns: File path to generated export
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sap_export_{timestamp}.csv"
            filepath = f"exports/{filename}"
            
            # Create exports directory if it doesn't exist
            import os
            os.makedirs("exports", exist_ok=True)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'EmployeeId', 'FirstName', 'Surname', 'JobTitle', 'Department',
                    'BasicSalary', 'TotalEarnings', 'TotalDeductions', 'NetPay',
                    'TotalEmployer', 'CTC', 'Status', 'SubmissionDate'
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
                        'SubmissionDate': package.get('submission_date')
                    })
            
            self.logger.info(f"SAP export file generated: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error generating SAP export file: {str(e)}")
            return ""
    
    def _get_auth_token(self) -> str:
        """Get SAP authentication token"""
        import base64
        credentials = f"{self.sap_username}:{self.sap_password}"
        return base64.b64encode(credentials.encode()).decode()
    
    def _transform_employee_data(self, sap_data: Dict) -> Dict:
        """Transform SAP employee data to calculator format"""
        return {
            'employee_id': sap_data.get('EmployeeId'),
            'first_name': sap_data.get('FirstName'),
            'surname': sap_data.get('LastName'),
            'id_number': sap_data.get('IdNumber'),
            'email': sap_data.get('Email'),
            'job_title': sap_data.get('JobTitle'),
            'department': sap_data.get('Department'),
            'start_date': sap_data.get('StartDate'),
            'age': sap_data.get('Age')
        }
    
    def _transform_salary_data(self, sap_data: Dict) -> Dict:
        """Transform SAP salary data to calculator format"""
        return {
            'basic_salary': sap_data.get('BasicSalary', 0),
            'allowances': sap_data.get('Allowances', []),
            'deductions': sap_data.get('Deductions', []),
            'employer_contributions': sap_data.get('EmployerContributions', []),
            'ctc': sap_data.get('CTC', 0)
        }
    
    def _transform_to_sap_format(self, calculator_data: Dict) -> Dict:
        """Transform calculator data to SAP format"""
        return {
            'BasicSalary': calculator_data.get('basic_salary'),
            'Allowances': calculator_data.get('earnings', []),
            'Deductions': calculator_data.get('deductions', []),
            'EmployerContributions': calculator_data.get('employer', []),
            'CTC': calculator_data.get('ctc_total_val'),
            'NetPay': calculator_data.get('net_pay_val')
        }

# Configuration example
SAP_CONFIG = {
    'base_url': 'https://your-sap-system.com',
    'username': 'your_username',
    'password': 'your_password',
    'client': '100'
} 