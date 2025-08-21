from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

class EmployeeAccess:
    """Employee access management for Package Builder"""
    
    def __init__(self):
        self.access_file = 'employee_access.json'
        self.load_access_data()
    
    def load_access_data(self):
        """Load employee access data from file"""
        if os.path.exists(self.access_file):
            with open(self.access_file, 'r') as f:
                self.access_data = json.load(f)
        else:
            self.access_data = []
    
    def save_access_data(self):
        """Save employee access data to file"""
        with open(self.access_file, 'w') as f:
            json.dump(self.access_data, f, indent=2)
    
    def create_employee_access(self, employee_id: str, grade_band: str, 
                              access_period_days: int = 30) -> Dict:
        """Create new employee access for Package Builder"""
        access_record = {
            'employee_id': employee_id,
            'grade_band': grade_band,
            'username': f"{employee_id.lower()}",
            'password': self._generate_password(),
            'access_granted': datetime.now().isoformat(),
            'access_expires': (datetime.now() + timedelta(days=access_period_days)).isoformat(),
            'status': 'ACTIVE',
            'package_submitted': False,
            'submission_date': None,
            'last_login': None
        }
        
        self.access_data.append(access_record)
        self.save_access_data()
        return access_record
    
    def validate_employee_access(self, username: str, password: str) -> Optional[Dict]:
        """Validate employee login credentials"""
        for access in self.access_data:
            if (access['username'] == username and 
                access['password'] == password and 
                access['status'] == 'ACTIVE' and
                datetime.fromisoformat(access['access_expires']) > datetime.now()):
                
                # Update last login
                access['last_login'] = datetime.now().isoformat()
                self.save_access_data()
                return access
        
        return None
    
    def revoke_employee_access(self, employee_id: str):
        """Revoke employee access after package submission or expiration"""
        for access in self.access_data:
            if access['employee_id'] == employee_id:
                access['status'] = 'REVOKED'
                access['access_expires'] = datetime.now().isoformat()
                self.save_access_data()
                break
    
    def get_active_employees(self) -> List[Dict]:
        """Get all employees with active access"""
        return [access for access in self.access_data if access['status'] == 'ACTIVE']
    
    def get_pending_submissions(self) -> List[Dict]:
        """Get employees who haven't submitted packages yet"""
        return [access for access in self.access_data 
                if access['status'] == 'ACTIVE' and not access['package_submitted']]
    
    def get_all_employees(self) -> List[Dict]:
        """Get all employees with access"""
        return self.access_data
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict]:
        """Get employee access details by employee ID"""
        for access in self.access_data:
            if access['employee_id'] == employee_id:
                return access
        return None
    
    def clear_all_access(self):
        """Clear all employee access data"""
        self.access_data = []
        self.save_access_data()
    
    def _generate_password(self) -> str:
        """Generate a random password for employee access"""
        import random
        import string
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(8))

class PackageManager:
    """Package management for TCTC modeling"""
    
    def __init__(self):
        self.packages_file = 'employee_packages.json'
        self.sap_uploads_file = 'sap_uploads.json'
        self.load_data()
    
    def load_data(self):
        """Load package and SAP upload data"""
        # Load employee packages
        if os.path.exists(self.packages_file):
            with open(self.packages_file, 'r') as f:
                self.packages = json.load(f)
        else:
            self.packages = []
        
        # Load SAP uploads
        if os.path.exists(self.sap_uploads_file):
            with open(self.sap_uploads_file, 'r') as f:
                self.sap_uploads = json.load(f)
        else:
            self.sap_uploads = []
    
    def save_data(self):
        """Save package and SAP upload data"""
        with open(self.packages_file, 'w') as f:
            json.dump(self.packages, f, indent=2)
        
        with open(self.sap_uploads_file, 'w') as f:
            json.dump(self.sap_uploads, f, indent=2)
    
    def upload_sap_data(self, filename: str, upload_date: str, 
                        employee_data: List[Dict]) -> Dict:
        """Upload SAP Excel data for employee packages"""
        upload_record = {
            'id': len(self.sap_uploads) + 1,
            'filename': filename,
            'upload_date': upload_date,
            'status': 'UPLOADED',
            'employee_count': len(employee_data),
            'employee_data': employee_data
        }
        
        self.sap_uploads.append(upload_record)
        self.save_data()
        return upload_record
    
    def create_employee_package(self, employee_id: str, sap_data: Dict, 
                               tctc_limit: float) -> Dict:
        """Create initial package from SAP data using actual SAP headers"""
        package = {
            'employee_id': employee_id,
            'sap_upload_id': sap_data.get('upload_id'),
            'tctc_limit': tctc_limit,
            'current_tctc': 0,
            'sap_data': sap_data,  # Store original SAP data
            'package_components': {
                'basic_salary': sap_data.get('TPE', 0),  # Total Pensionable Emolument
                'provident_fund': sap_data.get('pension', 0),
                'provident_fund_option': sap_data.get('PENSIONOPTION', ''),
                'car_allowance': sap_data.get('CAR', 0),
                'cellphone_allowance': sap_data.get('CELLPHONEALLOWANCE', 0),
                'data_service_allowance': sap_data.get('DATASERVICEALLOWANCE', 0),
                'housing_allowance': sap_data.get('HOUSING', 0),
                'medical_aid': sap_data.get('MEDICAL', 0),
                'medical_aid_option': sap_data.get('MEDICALOPTION', ''),
                'bonus': sap_data.get('BONUSPROVISION', 0),
                'other_allowances': sap_data.get('CASH', 0),
                'critical_skills': sap_data.get('CRITICALSKILLS', 0),
                'uif': sap_data.get('UIF', 0),
                'group_life': sap_data.get('GROUPLIFEEECONTRIBUTION', 0)
            },
            'employee_info': {
                'surname': sap_data.get('SURNAME', ''),
                'firstname': sap_data.get('FIRSTNAME', ''),
                'title': sap_data.get('TITLE', ''),
                'band': sap_data.get('BAND', ''),
                'cost_center': sap_data.get('CostCenter', ''),
                'department': sap_data.get('DEPARTMENT', ''),
                'position': sap_data.get('JOBSHORT', ''),
                'grade_band': sap_data.get('BAND', ''),
                'employee_group': sap_data.get('EMPLOYEEGROUPDESCRIPTION', ''),
                'employee_subgroup': sap_data.get('EMPLOYEESUBGROUPDESCRIPTION', '')
            },
            'status': 'DRAFT',
            'created_date': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat(),
            'submitted_date': None,
            'net_pay_calculation': None
        }
        
        # Calculate initial TCTC
        package['current_tctc'] = self._calculate_tctc(package['package_components'])
        
        self.packages.append(package)
        self.save_data()
        return package
    
    def update_employee_package(self, employee_id: str, updates: Dict) -> Optional[Dict]:
        """Update employee package with new values"""
        for package in self.packages:
            if package['employee_id'] == employee_id:
                # Update package components
                for key, value in updates.items():
                    if key in package['package_components']:
                        package['package_components'][key] = value
                
                # Recalculate TCTC
                package['current_tctc'] = self._calculate_tctc(package['package_components'])
                package['last_modified'] = datetime.now().isoformat()
                
                self.save_data()
                return package
        
        return None
    
    def submit_employee_package(self, employee_id: str) -> Optional[Dict]:
        """Submit completed employee package"""
        for package in self.packages:
            if package['employee_id'] == employee_id:
                package['status'] = 'SUBMITTED'
                package['submitted_date'] = datetime.now().isoformat()
                
                # Calculate final net pay
                package['net_pay_calculation'] = self._calculate_net_pay(package)
                
                self.save_data()
                return package
        
        return None
    
    def get_employee_package(self, employee_id: str) -> Optional[Dict]:
        """Get package for specific employee"""
        for package in self.packages:
            if package['employee_id'] == employee_id:
                return package
        return None
    
    def get_all_packages(self) -> List[Dict]:
        """Get all employee packages"""
        return self.packages
    
    def get_submitted_packages(self) -> List[Dict]:
        """Get all submitted packages"""
        return [p for p in self.packages if p['status'] == 'SUBMITTED']
    
    def export_packages_for_sap(self) -> List[Dict]:
        """Export submitted packages in SAP format"""
        submitted_packages = self.get_submitted_packages()
        export_data = []
        
        for package in submitted_packages:
            export_record = {
                'employee_id': package['employee_id'],
                'tctc_limit': package['tctc_limit'],
                'final_tctc': package['current_tctc'],
                'basic_salary': package['package_components']['basic_salary'],
                'provident_fund': package['package_components']['provident_fund'],
                'car_allowance': package['package_components']['car_allowance'],
                'cellphone_allowance': package['package_components']['cellphone_allowance'],
                'data_service_allowance': package['package_components']['data_service_allowance'],
                'housing_allowance': package['package_components']['housing_allowance'],
                'medical_aid': package['package_components']['medical_aid'],
                'medical_aid_option': package['package_components']['medical_aid_option'],
                'bonus': package['package_components']['bonus'],
                'net_pay': package['net_pay_calculation']['take_home'] if package['net_pay_calculation'] else 0,
                'submission_date': package['submitted_date']
            }
            export_data.append(export_record)
        
        return export_data
    
    def clear_sap_uploads(self):
        """Clear all SAP upload data"""
        self.sap_uploads = []
        self.save_data()
    
    def clear_all_packages(self):
        """Clear all employee packages"""
        self.packages = []
        self.save_data()
    
    def _calculate_tctc(self, components: Dict) -> float:
        """Calculate total cost to company from package components"""
        tctc = 0
        tctc += components.get('basic_salary', 0)
        tctc += components.get('car_allowance', 0)
        tctc += components.get('cellphone_allowance', 0)
        tctc += components.get('data_service_allowance', 0)
        tctc += components.get('housing_allowance', 0)
        tctc += components.get('medical_aid', 0)
        tctc += components.get('bonus', 0)
        
        # Add other allowances (CASH field is a number, not a list)
        other_allowances = components.get('other_allowances', 0)
        if isinstance(other_allowances, (int, float)):
            tctc += other_allowances
        elif isinstance(other_allowances, list):
            for allowance in other_allowances:
                tctc += allowance.get('value', 0)
        
        return round(tctc, 2)
    
    def _calculate_net_pay(self, package: Dict) -> Dict:
        """Calculate net pay based on package components"""
        # This will integrate with the existing SARS calculation logic
        # For now, return a placeholder
        return {
            'gross_pay': package['current_tctc'],
            'tax': 0,
            'deductions': 0,
            'take_home': package['current_tctc']
        }

class NotificationManager:
    """Manage notifications for package submissions"""
    
    def __init__(self):
        self.notifications_file = 'notifications.json'
        self.load_notifications()
    
    def load_notifications(self):
        """Load notifications from file"""
        if os.path.exists(self.notifications_file):
            with open(self.notifications_file, 'r') as f:
                self.notifications = json.load(f)
        else:
            self.notifications = []
    
    def save_notifications(self):
        """Save notifications to file"""
        with open(self.notifications_file, 'w') as f:
            json.dump(self.notifications, f, indent=2)
    
    def create_notification(self, type: str, message: str, 
                           employee_id: str = None, admin_only: bool = False) -> Dict:
        """Create a new notification"""
        notification = {
            'id': len(self.notifications) + 1,
            'type': type,
            'message': message,
            'employee_id': employee_id,
            'admin_only': admin_only,
            'created_date': datetime.now().isoformat(),
            'read': False
        }
        
        self.notifications.append(notification)
        self.save_notifications()
        return notification
    
    def get_admin_notifications(self) -> List[Dict]:
        """Get notifications for admin users"""
        return [n for n in self.notifications if n['admin_only']]
    
    def get_employee_notifications(self, employee_id: str) -> List[Dict]:
        """Get notifications for specific employee"""
        return [n for n in self.notifications 
                if n['employee_id'] == employee_id and not n['admin_only']]
    
    def mark_as_read(self, notification_id: int):
        """Mark notification as read"""
        for notification in self.notifications:
            if notification['id'] == notification_id:
                notification['read'] = True
                break
        self.save_notifications()

class EmailLogger:
    """Logs all email operations for audit purposes"""
    
    def __init__(self, log_file='email_logs.json'):
        self.log_file = log_file
        self.logs = self.load_logs()
    
    def load_logs(self) -> List[Dict]:
        """Load existing email logs from file"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading email logs: {str(e)}")
        return []
    
    def save_logs(self):
        """Save email logs to file"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving email logs: {str(e)}")
    
    def log_email_operation(self, operation_type: str, recipients: List[str], subject: str, 
                           success: bool, details: str = "", error_message: str = ""):
        """Log an email operation"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation_type': operation_type,  # 'credentials', 'notification', etc.
            'recipients': recipients,
            'subject': subject,
            'success': success,
            'details': details,
            'error_message': error_message if not success else "",
            'admin_user': 'system'  # Could be enhanced to track actual admin user
        }
        
        self.logs.append(log_entry)
        self.save_logs()
        
        # Also log to console for debugging
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"Email {operation_type} {status} - Recipients: {recipients}")
        if not success and error_message:
            logger.error(f"Email error: {error_message}")
    
    def get_logs_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get logs within a date range"""
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            filtered_logs = []
            for log in self.logs:
                log_time = datetime.fromisoformat(log['timestamp'])
                if start <= log_time <= end:
                    filtered_logs.append(log)
            
            return filtered_logs
        except Exception as e:
            logger.error(f"Error filtering logs by date: {str(e)}")
            return []
    
    def get_logs_by_operation(self, operation_type: str) -> List[Dict]:
        """Get logs for a specific operation type"""
        return [log for log in self.logs if log['operation_type'] == operation_type]
    
    def get_success_rate(self) -> Dict[str, float]:
        """Calculate success rate for different operation types"""
        stats = {}
        for log in self.logs:
            op_type = log['operation_type']
            if op_type not in stats:
                stats[op_type] = {'total': 0, 'success': 0}
            
            stats[op_type]['total'] += 1
            if log['success']:
                stats[op_type]['success'] += 1
        
        # Calculate percentages
        for op_type, counts in stats.items():
            if counts['total'] > 0:
                stats[op_type]['success_rate'] = (counts['success'] / counts['total']) * 100
            else:
                stats[op_type]['success_rate'] = 0
        
        return stats
    
    def export_logs_csv(self, logs: List[Dict] = None) -> str:
        """Export logs to CSV format for download"""
        if logs is None:
            logs = self.logs
        
        if not logs:
            return ""
        
        # Create CSV content
        csv_lines = []
        
        # Header
        headers = ['Timestamp', 'Operation Type', 'Recipients', 'Subject', 'Success', 'Details', 'Error Message', 'Admin User']
        csv_lines.append(','.join(f'"{h}"' for h in headers))
        
        # Data rows
        for log in logs:
            row = [
                log['timestamp'],
                log['operation_type'],
                '; '.join(log['recipients']),
                log['subject'],
                'Yes' if log['success'] else 'No',
                log['details'],
                log['error_message'],
                log['admin_user']
            ]
            csv_lines.append(','.join(f'"{str(field)}"' for field in row))
        
        return '\n'.join(csv_lines)
    
    def clear_logs(self):
        """Clear all email logs"""
        self.logs = []
        self.save_logs()
        logger.info("Email logs cleared")


# Initialize email logger
email_logger = EmailLogger()

class SMTPConfig:
    """Manages SMTP configuration for email functionality"""
    
    def __init__(self, config_file='smtp_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load SMTP configuration from file"""
        default_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'username': '',
            'password': '',
            'from_email': '',
            'from_name': 'Rand Water Package Builder',
            'enabled': False
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    default_config.update(loaded_config)
        except Exception as e:
            logger.error(f"Error loading SMTP config: {str(e)}")
        
        return default_config
    
    def save_config(self):
        """Save SMTP configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("SMTP configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving SMTP config: {str(e)}")
    
    def update_config(self, new_config: Dict):
        """Update SMTP configuration"""
        self.config.update(new_config)
        self.save_config()
    
    def test_connection(self) -> Dict[str, any]:
        """Test SMTP connection with current configuration"""
        if not self.config['enabled']:
            return {'success': False, 'error': 'SMTP is not enabled'}
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            # Create test message
            msg = MIMEText('This is a test email from Rand Water Package Builder')
            msg['Subject'] = 'SMTP Test - Rand Water Package Builder'
            msg['From'] = f"{self.config['from_name']} <{self.config['from_email']}>"
            msg['To'] = self.config['from_email']  # Send to self for testing
            
            # Connect to SMTP server
            if self.config['use_tls']:
                server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
                server.starttls()
            else:
                server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            
            # Login
            server.login(self.config['username'], self.config['password'])
            
            # Send test email
            server.send_message(msg)
            server.quit()
            
            return {'success': True, 'message': 'SMTP connection test successful'}
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"SMTP connection test failed: {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def get_config(self) -> Dict:
        """Get current SMTP configuration (without password)"""
        safe_config = self.config.copy()
        if safe_config.get('password'):
            safe_config['password'] = '••••••••'  # Hide password
        return safe_config


# Initialize SMTP config
smtp_config = SMTPConfig()
