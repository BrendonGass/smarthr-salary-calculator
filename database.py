import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class RandwaterDatabase:
    """SQLite database manager for Randwater Calculator with full historic tracking"""
    
    def __init__(self, db_path: str = 'randwater_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                profile TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                status TEXT DEFAULT 'active',
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                login_count INTEGER DEFAULT 0
            )
        ''')
        
        # SAP uploads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sap_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_filename TEXT,
                file_path TEXT NOT NULL,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                uploaded_by TEXT,
                employee_count INTEGER,
                file_size INTEGER,
                status TEXT DEFAULT 'ACTIVE',
                deleted_date DATETIME,
                deleted_by TEXT
            )
        ''')
        
        # Employees table (from SAP data)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                upload_id INTEGER,
                surname TEXT,
                firstname TEXT,
                title TEXT,
                band TEXT,
                cost_center TEXT,
                department TEXT,
                position TEXT,
                grade_band TEXT,
                employee_group TEXT,
                employee_subgroup TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (upload_id) REFERENCES sap_uploads (id)
            )
        ''')
        
        # Employee packages table (TCTC modeling)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employee_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                upload_id INTEGER,
                basic_salary REAL DEFAULT 0,
                housing_allowance REAL DEFAULT 0,
                transport_allowance REAL DEFAULT 0,
                medical_aid REAL DEFAULT 0,
                pension_fund REAL DEFAULT 0,
                group_life REAL DEFAULT 0,
                car_allowance REAL DEFAULT 0,
                cellphone_allowance REAL DEFAULT 0,
                data_service_allowance REAL DEFAULT 0,
                bonus REAL DEFAULT 0,
                other_allowances REAL DEFAULT 0,
                critical_skills REAL DEFAULT 0,
                uif REAL DEFAULT 0,
                current_tctc REAL DEFAULT 0,
                target_tctc REAL DEFAULT 0,
                status TEXT DEFAULT 'DRAFT',
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
                submitted_date DATETIME,
                submitted_by TEXT,
                FOREIGN KEY (upload_id) REFERENCES sap_uploads (id)
            )
        ''')
        
        # Package history table (track all changes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS package_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                package_id INTEGER,
                employee_id TEXT,
                field_name TEXT,
                old_value REAL,
                new_value REAL,
                change_reason TEXT,
                changed_by TEXT,
                change_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (package_id) REFERENCES employee_packages (id)
            )
        ''')
        
        # Tax settings history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tax_settings_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_name TEXT,
                old_value REAL,
                new_value REAL,
                changed_by TEXT,
                change_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                effective_date DATETIME
            )
        ''')
        
        # Audit log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT,
                table_name TEXT,
                record_id TEXT,
                old_data TEXT,
                new_data TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Employee access table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employee_access (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE NOT NULL,
                access_granted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                access_granted_by TEXT,
                status TEXT DEFAULT 'active',
                last_access DATETIME,
                access_count INTEGER DEFAULT 0
            )
        ''')
        
        # System settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                setting_type TEXT,
                description TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {self.db_path}")
    
    def migrate_from_json(self):
        """Migrate existing JSON data to SQL database"""
        print("🔄 Starting migration from JSON files to SQL database...")
        
        # Migrate users
        self._migrate_users()
        
        # Migrate SAP uploads
        self._migrate_sap_uploads()
        
        # Migrate employee packages
        self._migrate_employee_packages()
        
        # Migrate employee access
        self._migrate_employee_access()
        
        print("✅ Migration completed successfully!")
    
    def _migrate_users(self):
        """Migrate user data"""
        # Default system users
        default_users = [
            {
                'username': 'superadmin',
                'password': 'SuperSecret2024!',
                'profile': 'superadmin',
                'full_name': 'System Super Administrator',
                'email': 'superadmin@randwater.co.za'
            },
            {
                'username': 'randwateradmin',
                'password': 'RandWater2024!',
                'profile': 'admin',
                'full_name': 'Rand Water Administrator',
                'email': 'admin@randwater.co.za'
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for user in default_users:
            cursor.execute('''
                INSERT OR REPLACE INTO users (username, password, profile, full_name, email)
                VALUES (?, ?, ?, ?, ?)
            ''', (user['username'], user['password'], user['profile'], 
                  user['full_name'], user['email']))
        
        conn.commit()
        conn.close()
        print("✅ Users migrated")
    
    def _migrate_sap_uploads(self):
        """Migrate SAP upload data"""
        json_file = 'sap_uploads.json'
        if not os.path.exists(json_file):
            print(f"⚠️  {json_file} not found, skipping SAP uploads migration")
            return
        
        with open(json_file, 'r') as f:
            uploads = json.load(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for upload in uploads:
            cursor.execute('''
                INSERT INTO sap_uploads 
                (filename, file_path, upload_date, employee_count, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                upload.get('filename', ''),
                f"uploads/{upload.get('filename', '')}",
                upload.get('upload_date', datetime.now().isoformat()),
                upload.get('employee_count', 0),
                upload.get('status', 'ACTIVE')
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ {len(uploads)} SAP uploads migrated")
    
    def _migrate_employee_packages(self):
        """Migrate employee package data"""
        json_file = 'employee_packages.json'
        if not os.path.exists(json_file):
            print(f"⚠️  {json_file} not found, skipping employee packages migration")
            return
        
        with open(json_file, 'r') as f:
            packages = json.load(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for package in packages:
            components = package.get('package_components', {})
            cursor.execute('''
                INSERT INTO employee_packages 
                (employee_id, basic_salary, housing_allowance, transport_allowance,
                 medical_aid, pension_fund, group_life, car_allowance, 
                 cellphone_allowance, data_service_allowance, bonus, 
                 other_allowances, critical_skills, uif, current_tctc, 
                 target_tctc, status, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                package.get('employee_id', ''),
                components.get('basic_salary', 0),
                components.get('housing_allowance', 0),
                components.get('transport_allowance', 0),
                components.get('medical_aid', 0),
                components.get('pension_fund', 0),
                components.get('group_life', 0),
                components.get('car_allowance', 0),
                components.get('cellphone_allowance', 0),
                components.get('data_service_allowance', 0),
                components.get('bonus', 0),
                components.get('other_allowances', 0),
                components.get('critical_skills', 0),
                components.get('uif', 0),
                package.get('current_tctc', 0),
                package.get('target_tctc', 0),
                package.get('status', 'DRAFT'),
                package.get('created_date', datetime.now().isoformat())
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ {len(packages)} employee packages migrated")
    
    def _migrate_employee_access(self):
        """Migrate employee access data"""
        json_file = 'employee_access.json'
        if not os.path.exists(json_file):
            print(f"⚠️  {json_file} not found, skipping employee access migration")
            return
        
        with open(json_file, 'r') as f:
            access_data = json.load(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for access in access_data:
            cursor.execute('''
                INSERT INTO employee_access 
                (employee_id, access_granted_date, status)
                VALUES (?, ?, ?)
            ''', (
                access.get('employee_id', ''),
                access.get('access_granted', datetime.now().isoformat()),
                access.get('status', 'active')
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ {len(access_data)} employee access records migrated")
    
    # Data access methods
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def log_user_login(self, username: str):
        """Log user login"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
            WHERE username = ?
        ''', (username,))
        
        conn.commit()
        conn.close()
    
    def save_sap_upload(self, filename: str, file_path: str, uploaded_by: str, 
                       employee_count: int, file_size: int) -> int:
        """Save SAP upload record and return upload ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sap_uploads 
            (filename, file_path, uploaded_by, employee_count, file_size)
            VALUES (?, ?, ?, ?, ?)
        ''', (filename, file_path, uploaded_by, employee_count, file_size))
        
        upload_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return upload_id
    
    def get_package_history(self, employee_id: str) -> List[Dict]:
        """Get complete history of package changes for an employee"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM package_history 
            WHERE employee_id = ? 
            ORDER BY change_date DESC
        ''', (employee_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def backup_database(self, backup_path: str = None):
        """Create a backup of the database"""
        if backup_path is None:
            backup_path = f"randwater_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        import shutil
        shutil.copy2(self.db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path

if __name__ == "__main__":
    # Initialize and migrate
    db = RandwaterDatabase()
    db.migrate_from_json()
    print("🎉 Database setup complete!")
