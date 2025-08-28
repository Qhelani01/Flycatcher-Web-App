# Simple user management for Flycatcher app
# In production, you'd use a proper database

# Demo users (in production, this would be a database)
DEMO_USERS = {
    "demo@flycatcher.com": {
        "password": "demo123",
        "name": "Demo User",
        "role": "user"
    },
    "admin@flycatcher.com": {
        "password": "admin123",
        "name": "Admin User",
        "role": "admin"
    }
}

def authenticate_user(email, password):
    """Authenticate a user with email and password"""
    if email in DEMO_USERS:
        user = DEMO_USERS[email]
        if user["password"] == password:
            return {
                "success": True,
                "user": {
                    "email": email,
                    "name": user["name"],
                    "role": user["role"]
                }
            }
    
    return {
        "success": False,
        "error": "Invalid email or password"
    }

def get_user_by_email(email):
    """Get user information by email"""
    if email in DEMO_USERS:
        user = DEMO_USERS[email]
        return {
            "email": email,
            "name": user["name"],
            "role": user["role"]
        }
    return None
