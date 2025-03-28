import json
from werkzeug.security import generate_password_hash
# User database (you may replace this with a proper database)
users = {
    'user1': {
        'username': 'user1',
        'password': generate_password_hash('password1'),
        'role': 'user'  # Assuming a default role for regular users
    },
    'user2': {
        'username': 'user2',
        'password': generate_password_hash('password2'),
        'role': 'user'  # Assuming a default role for regular users
    },
    'admin': {
        'username': 'admin',
        'password': generate_password_hash('admin'),
        'role': 'admin'  # Role set to 'admin' for admin user
    }
}

# Write user data to users.json
with open('users.json', 'w') as json_file:
    json.dump(users, json_file, indent=4)
