import time
from app.db.db import get_db

def add_post(user_id, filename, description, base64_image, mime_type):
    db = get_db()
    db.execute(
        "INSERT INTO images (user_id, name, description, base64_image, mime_type, uploaded_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, filename, description, base64_image, mime_type, int(time.time()))
    )
    db.commit()

def get_all_posts():
    db = get_db()
    post_rows = db.execute("""
        SELECT i.id, i.description, i.uploaded_at, u.username, i.base64_image, i.mime_type 
        FROM images i 
        JOIN users u ON i.user_id = u.id 
        ORDER BY i.uploaded_at DESC
    """).fetchall()
    
    return post_rows

def get_post_by_id(post_id,):
    db = get_db()
    return db.execute("SELECT base64_image, name, user_id, mime_type FROM images WHERE id = ?", (post_id,)).fetchone()

def update_post_image(post_id, image_blob, mime_type):
    db = get_db()
    db.execute("UPDATE images SET base64_image = ?, mime_type = ?, updated_at = ? WHERE id = ?", (image_blob, mime_type, int(time.time()), post_id))
    db.commit()

def update_post_description(post_id, description):
    db = get_db()
    db.execute("UPDATE images SET description = ?, updated_at = ? WHERE id = ?", (description, int(time.time()), post_id))
    db.commit()

# deletes post if post exists and user id matches
def delete_post(post_id, user_id):
    try:
        db = get_db()
        db.execute("DELETE FROM images WHERE id = ? AND user_id = ?", (post_id, user_id))
        db.commit()
        return True
    except Exception as e:
        print(f'[ERROR] Failed to delete post ID: {post_id} for user ID: {user_id}, error: {e}')
        return False