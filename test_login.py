#!/usr/bin/env python3
"""
Test script to verify login credentials
"""

from werkzeug.security import check_password_hash
import json

def test_login():
    print("=== LOGIN CREDENTIAL TEST ===")
    
    # Load system users
    try:
        with open('system_users.json', 'r') as f:
            users = json.load(f)
        print(f"✅ Loaded {len(users)} users from system_users.json")
    except Exception as e:
        print(f"❌ Error loading system_users.json: {e}")
        return
    
    # Test credentials
    test_username = "RandWaterAdmin"
    test_password = "Anna2537"
    
    print(f"\nTesting credentials:")
    print(f"Username: {test_username}")
    print(f"Password: {test_password}")
    
    # Check each user
    for i, user in enumerate(users):
        username = user.get('username', '')
        password_hash = user.get('password', '')
        profile = user.get('profile', '')
        status = user.get('status', '')
        
        print(f"\nUser {i+1}:")
        print(f"  Username: '{username}'")
        print(f"  Profile: {profile}")
        print(f"  Status: {status}")
        print(f"  Password hash: {password_hash[:50]}..." if len(password_hash) > 50 else f"  Password: {password_hash}")
        
        # Check username match (case insensitive)
        if username.lower() == test_username.lower():
            print(f"  ✅ USERNAME MATCHES!")
            
            # Check password
            is_hashed = ':' in password_hash
            print(f"  Is hashed: {is_hashed}")
            
            if is_hashed:
                try:
                    password_valid = check_password_hash(password_hash, test_password)
                    print(f"  Password check result: {password_valid}")
                    if password_valid:
                        print(f"  🎉 LOGIN SUCCESS!")
                        return True
                except Exception as e:
                    print(f"  ❌ Password check error: {e}")
            else:
                password_valid = (password_hash == test_password)
                print(f"  Plain text password match: {password_valid}")
                if password_valid:
                    print(f"  🎉 LOGIN SUCCESS!")
                    return True
        else:
            print(f"  ❌ Username doesn't match")
    
    print(f"\n❌ LOGIN FAILED - No matching credentials found")
    return False

if __name__ == "__main__":
    test_login()
