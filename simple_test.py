from werkzeug.security import check_password_hash
import json

# Load users
users = json.load(open('system_users.json'))
print('Number of users:', len(users))

# Test the RandWaterAdmin user (index 1)
user = users[1]
print('Username:', user['username'])
print('Profile:', user['profile'])
print('Password hash:', user['password'][:50] + '...')

# Test password
result = check_password_hash(user['password'], 'Anna2537')
print('Password check result:', result)

if result:
    print('SUCCESS: Password Anna2537 is correct!')
else:
    print('FAILED: Password Anna2537 is incorrect!')
