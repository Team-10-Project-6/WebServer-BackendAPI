from flask import g
from app.db.db import get_db

def get_or_create_user(auth0_sub):
    db = get_db()
    
    user = db.execute("SELECT id, username FROM users WHERE auth0_sub = ?", (auth0_sub,)).fetchone()
    
    if user is None:
        # Get email from token claims
        email = g.user_claims.get('email')
        print(f'[INFO] Creating new user with email: {email}')
        
        db.execute("INSERT INTO users (auth0_sub, username) VALUES (?, ?)", (auth0_sub, email))
        db.commit()
        
        user = db.execute("SELECT id, username FROM users WHERE auth0_sub = ?", (auth0_sub,)).fetchone()
        print(f'[INFO] Created user - ID: {user["id"]}, Username: {user["username"]}')
    else:
        print(f'[INFO] Found existing user - ID: {user["id"]}, Username: {user["username"]}')
    
    email = g.user_claims.get('email')
    print(f'[INFO] User email: {email}')
    
    return user["id"]

def get_user_by_id(user_id):
    db = get_db()
    return db.execute("SELECT id, username, auth0_sub FROM users WHERE id = ?", (user_id,)).fetchone()

# updates username for given user id
def update_username(user_id, new_username):
    db = get_db()
    
    # check if username exists
    existing = db.execute("SELECT id FROM users WHERE username = ? AND id != ?", (new_username, user_id)).fetchone()
    
    if existing:
        return False
        
    db.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, user_id))
    db.commit()
    return True