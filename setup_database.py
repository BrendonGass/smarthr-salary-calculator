#!/usr/bin/env python3
"""
Randwater Database Setup and Migration Script
Run this to convert from JSON files to SQLite database with full historic tracking
"""

import os
import json
import shutil
from datetime import datetime
from database import RandwaterDatabase

def backup_json_files():
    """Backup existing JSON files before migration"""
    backup_dir = f"json_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    json_files = [
        'sap_uploads.json',
        'employee_packages.json',
        'randwater_package_audit.json',
        'employee_access.json',
        'randwater_tax_settings.json'
    ]
    
    backed_up = []
    for file in json_files:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(backup_dir, file))
            backed_up.append(file)
    
    if backed_up:
        print(f"📁 Backed up {len(backed_up)} JSON files to: {backup_dir}")
        return backup_dir
    else:
        print("⚠️  No JSON files found to backup")
        return None

def setup_database():
    """Setup and initialize the SQLite database"""
    print("🚀 Setting up Randwater SQLite Database...")
    print("=" * 50)
    
    # Check if database already exists
    if os.path.exists('randwater_data.db'):
        response = input("⚠️  Database already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("❌ Setup cancelled")
            return False
        
        # Backup existing database
        backup_name = f"randwater_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2('randwater_data.db', backup_name)
        print(f"💾 Existing database backed up as: {backup_name}")
    
    # Backup JSON files
    json_backup_dir = backup_json_files()
    
    # Initialize database
    db = RandwaterDatabase()
    
    # Migrate existing data
    print("\n🔄 Migrating existing data...")
    db.migrate_from_json()
    
    # Create initial backup
    initial_backup = db.backup_database("randwater_initial_backup.db")
    
    print("\n✅ Database setup completed successfully!")
    print("=" * 50)
    print(f"📊 Database file: randwater_data.db")
    print(f"💾 Initial backup: {initial_backup}")
    if json_backup_dir:
        print(f"📁 JSON backup: {json_backup_dir}")
    
    print("\n🔧 Next steps:")
    print("1. Update your Randwater calculator to use the new database")
    print("2. Test all functionality to ensure data integrity")
    print("3. Set up regular database backups")
    
    return True

def show_database_info():
    """Show information about the current database"""
    if not os.path.exists('randwater_data.db'):
        print("❌ No database found. Run setup first.")
        return
    
    import sqlite3
    
    conn = sqlite3.connect('randwater_data.db')
    cursor = conn.cursor()
    
    print("📊 Randwater Database Information")
    print("=" * 40)
    
    # Get table sizes
    tables = [
        'users', 'sap_uploads', 'employees', 'employee_packages',
        'package_history', 'tax_settings_history', 'audit_log',
        'employee_access', 'system_settings'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table:20}: {count:6} records")
        except sqlite3.OperationalError:
            print(f"{table:20}: Table not found")
    
    # Database file size
    db_size = os.path.getsize('randwater_data.db')
    print(f"\nDatabase size: {db_size:,} bytes ({db_size/1024/1024:.2f} MB)")
    
    # Recent activity
    cursor.execute('''
        SELECT COUNT(*) FROM audit_log 
        WHERE timestamp >= datetime('now', '-7 days')
    ''')
    recent_activity = cursor.fetchone()[0]
    print(f"Recent activity (7 days): {recent_activity} actions")
    
    conn.close()

def create_backup():
    """Create a manual backup of the database"""
    if not os.path.exists('randwater_data.db'):
        print("❌ No database found to backup")
        return
    
    db = RandwaterDatabase()
    backup_path = db.backup_database()
    print(f"✅ Backup created: {backup_path}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            setup_database()
        elif command == "info":
            show_database_info()
        elif command == "backup":
            create_backup()
        else:
            print("Unknown command. Use: setup, info, or backup")
    else:
        print("Randwater Database Management")
        print("=" * 30)
        print("Available commands:")
        print("  python setup_database.py setup   - Initialize database and migrate data")
        print("  python setup_database.py info    - Show database information")
        print("  python setup_database.py backup  - Create manual backup")
        print()
        
        # Default to setup if no database exists
        if not os.path.exists('randwater_data.db'):
            print("No database found. Running setup...")
            setup_database()
        else:
            show_database_info()
