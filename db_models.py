"""
Database models and data access layer for Randwater Calculator
Provides SQLite-based data management with full historic tracking
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from database import RandwaterDatabase

class DatabaseManager:
    """Enhanced database manager with Randwater-specific operations"""
    
    def __init__(self):
        self.db = RandwaterDatabase()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data"""
        user = self.db.get_user(username.lower())
        if user and user['password'] == password and user['status'] == 'active':
            self.db.log_user_login(username.lower())
            return user
        return None
    
    def save_sap_upload_with_data(self, filename: str, file_path: str, 
                                 uploaded_by: str, employee_data: List[Dict]) -> int:
        """Save SAP upload with employee data"""
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        upload_id = self.db.save_sap_upload(
            filename=filename,
            file_path=file_path,
            uploaded_by=uploaded_by,
            employee_count=len(employee_data),
            file_size=file_size
        )
        
        # Save employee data
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for emp_data in employee_data:
            # Save employee info
            cursor.execute('''
                INSERT OR REPLACE INTO employees 
                (employee_id, upload_id, surname, firstname, title, band, 
                 cost_center, department, position, grade_band, 
                 employee_group, employee_subgroup)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                emp_data.get('EMPLOYEE', ''),
                upload_id,
                emp_data.get('SURNAME', ''),
                emp_data.get('FIRSTNAME', ''),
                emp_data.get('TITLE', ''),
                emp_data.get('BAND', ''),
                emp_data.get('CostCenter', ''),
                emp_data.get('DEPARTMENT', ''),
                emp_data.get('JOBSHORT', ''),
                emp_data.get('BAND', ''),
                emp_data.get('EMPLOYEEGROUPDESCRIPTION', ''),
                emp_data.get('EMPLOYEESUBGROUPDESCRIPTION', '')
            ))
            
            # Save initial package
            cursor.execute('''
                INSERT OR REPLACE INTO employee_packages 
                (employee_id, upload_id, basic_salary, housing_allowance, 
                 transport_allowance, medical_aid, pension_fund, group_life,
                 car_allowance, cellphone_allowance, data_service_allowance,
                 bonus, other_allowances, critical_skills, uif, current_tctc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                emp_data.get('EMPLOYEE', ''),
                upload_id,
                float(emp_data.get('BASIC', 0)),
                float(emp_data.get('HOUSING', 0)),
                float(emp_data.get('TRANSPORT', 0)),
                float(emp_data.get('MEDICAL', 0)),
                float(emp_data.get('PENSIONCONTRIBUTIONFUND', 0)),
                float(emp_data.get('GROUPLIFEEECONTRIBUTION', 0)),
                float(emp_data.get('CAR', 0)),
                float(emp_data.get('CELLPHONEALLOWANCE', 0)),
                float(emp_data.get('DATASERVICEALLOWANCE', 0)),
                float(emp_data.get('BONUSPROVISION', 0)),
                float(emp_data.get('CASH', 0)),
                float(emp_data.get('CRITICALSKILLS', 0)),
                float(emp_data.get('UIF', 0)),
                self._calculate_tctc(emp_data)
            ))
        
        conn.commit()
        conn.close()
        
        # Log the upload
        self._log_audit('SAP_UPLOAD', 'sap_uploads', str(upload_id), 
                       uploaded_by, f"Uploaded {len(employee_data)} employees")
        
        return upload_id
    
    def _calculate_tctc(self, emp_data: Dict) -> float:
        """Calculate Total Cost to Company"""
        components = [
            'BASIC', 'HOUSING', 'TRANSPORT', 'MEDICAL', 
            'PENSIONCONTRIBUTIONFUND', 'GROUPLIFEEECONTRIBUTION',
            'CAR', 'CELLPHONEALLOWANCE', 'DATASERVICEALLOWANCE',
            'BONUSPROVISION', 'CASH', 'CRITICALSKILLS'
        ]
        return sum(float(emp_data.get(comp, 0)) for comp in components)
    
    def get_employee_package(self, employee_id: str) -> Optional[Dict]:
        """Get current employee package"""
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ep.*, e.surname, e.firstname, e.title, e.department
            FROM employee_packages ep
            LEFT JOIN employees e ON ep.employee_id = e.employee_id
            WHERE ep.employee_id = ?
            ORDER BY ep.last_modified DESC
            LIMIT 1
        ''', (employee_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def update_employee_package(self, employee_id: str, updates: Dict, 
                               updated_by: str, reason: str = "") -> bool:
        """Update employee package with full audit trail"""
        current_package = self.get_employee_package(employee_id)
        if not current_package:
            return False
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Record changes in history
        for field, new_value in updates.items():
            if field in current_package:
                old_value = current_package[field]
                if old_value != new_value:
                    cursor.execute('''
                        INSERT INTO package_history 
                        (package_id, employee_id, field_name, old_value, 
                         new_value, change_reason, changed_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        current_package['id'], employee_id, field,
                        float(old_value) if old_value else 0,
                        float(new_value) if new_value else 0,
                        reason, updated_by
                    ))
        
        # Update the package
        set_clause = ', '.join([f"{field} = ?" for field in updates.keys()])
        values = list(updates.values()) + [datetime.now().isoformat(), employee_id]
        
        cursor.execute(f'''
            UPDATE employee_packages 
            SET {set_clause}, last_modified = ?
            WHERE employee_id = ?
        ''', values)
        
        conn.commit()
        conn.close()
        
        # Log the update
        self._log_audit('PACKAGE_UPDATE', 'employee_packages', employee_id,
                       updated_by, f"Updated: {', '.join(updates.keys())}")
        
        return True
    
    def get_all_uploads(self) -> List[Dict]:
        """Get all SAP uploads with metadata"""
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT *, 
                   (SELECT COUNT(*) FROM employees WHERE upload_id = sap_uploads.id) as actual_employee_count
            FROM sap_uploads 
            WHERE status = 'ACTIVE'
            ORDER BY upload_date DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_employees_by_upload(self, upload_id: int) -> List[Dict]:
        """Get all employees from a specific upload"""
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.*, ep.current_tctc, ep.status as package_status
            FROM employees e
            LEFT JOIN employee_packages ep ON e.employee_id = ep.employee_id
            WHERE e.upload_id = ?
            ORDER BY e.surname, e.firstname
        ''', (upload_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def search_employees(self, search_term: str) -> List[Dict]:
        """Search employees by ID, name, or department"""
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        search_term = f"%{search_term}%"
        cursor.execute('''
            SELECT e.*, ep.current_tctc, ep.status as package_status
            FROM employees e
            LEFT JOIN employee_packages ep ON e.employee_id = ep.employee_id
            WHERE e.employee_id LIKE ? 
               OR e.surname LIKE ? 
               OR e.firstname LIKE ?
               OR e.department LIKE ?
            ORDER BY e.surname, e.firstname
            LIMIT 50
        ''', (search_term, search_term, search_term, search_term))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_audit_trail(self, employee_id: str = None, limit: int = 100) -> List[Dict]:
        """Get audit trail, optionally filtered by employee"""
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if employee_id:
            cursor.execute('''
                SELECT * FROM audit_log 
                WHERE record_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (employee_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM audit_log 
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def _log_audit(self, action: str, table_name: str, record_id: str,
                   user_id: str, details: str):
        """Log audit entry"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_log 
            (user_id, action, table_name, record_id, new_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, action, table_name, record_id, details))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self) -> Dict:
        """Get system statistics"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Total employees
        cursor.execute('SELECT COUNT(*) FROM employees')
        total_employees = cursor.fetchone()[0]
        
        # Total uploads
        cursor.execute("SELECT COUNT(*) FROM sap_uploads WHERE status = 'ACTIVE'")
        total_uploads = cursor.fetchone()[0]
        
        # Package statuses
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM employee_packages 
            GROUP BY status
        ''')
        package_stats = dict(cursor.fetchall())
        
        # Recent uploads
        cursor.execute('''
            SELECT COUNT(*) 
            FROM sap_uploads 
            WHERE upload_date >= datetime('now', '-7 days')
        ''')
        recent_uploads = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_employees': total_employees,
            'total_uploads': total_uploads,
            'package_stats': package_stats,
            'recent_uploads': recent_uploads
        }
    
    def backup_data(self) -> str:
        """Create a backup of all data"""
        return self.db.backup_database()

# Global database instance
db_manager = DatabaseManager()
