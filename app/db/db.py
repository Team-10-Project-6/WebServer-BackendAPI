import sqlite3
from flask import g

def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect("database.db")
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database tables"""
    db = get_db()
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, 
            username TEXT UNIQUE,
            auth0_sub TEXT UNIQUE
        )
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY, 
            user_id INTEGER, 
            name TEXT, 
            description TEXT, 
            data BLOB, 
            mime_type TEXT,
            uploaded_at INTEGER, 
            updated_at INTEGER
        )
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY, 
            image_id INTEGER, 
            user_id INTEGER, 
            comment_text TEXT, 
            created_at INTEGER,
            FOREIGN KEY(image_id) REFERENCES images(id)
        )
    """)
    
    db.commit()