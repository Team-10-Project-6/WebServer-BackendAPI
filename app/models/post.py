import time
from app.db.db import get_db

def create_post(user_id, filename, description, image_blob):
    db = get_db()
    db.execute(
        "INSERT INTO images (user_id, name, description, data, uploaded_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, filename, description, image_blob, int(time.time()))
    )
    db.commit()

def get_all_posts():
    db = get_db()
    post_rows = db.execute("""
        SELECT i.id, i.description, i.uploaded_at, u.username 
        FROM images i 
        JOIN users u ON i.user_id = u.id 
        ORDER BY i.uploaded_at DESC
    """).fetchall()
    
    return post_rows

def get_post_by_id(post_id):
    db = get_db()
    return db.execute("SELECT data, name FROM images WHERE id = ?", (post_id,)).fetchone()