import time
from utils.db import get_db

def create_comment(image_id, user_id, comment_text):
    db = get_db()
    db.execute(
        "INSERT INTO comments (image_id, user_id, comment_text, created_at) VALUES (?, ?, ?, ?)",
        (image_id, user_id, comment_text, int(time.time()))
    )
    db.commit()

def get_comments_for_post(post_id):
    db = get_db()
    return db.execute("""
        SELECT c.comment_text, u.username 
        FROM comments c 
        JOIN users u ON c.user_id = u.id 
        WHERE c.image_id = ?
    """, (post_id,)).fetchall()