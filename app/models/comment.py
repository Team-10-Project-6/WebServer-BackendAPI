import time
from app.db.db import get_db

def create_comment(image_id, user_id, comment_text):
    """
    Creates a new comment for a specific post/image.

    @param image_id The ID of the image/post being commented on.
    @param user_id The ID of the user creating the comment.
    @param comment_text The text content of the comment.
    """
    db = get_db()
    db.execute(
        "INSERT INTO comments (image_id, user_id, comment_text, created_at) VALUES (?, ?, ?, ?)",
        (image_id, user_id, comment_text, int(time.time()))
    )
    db.commit()

def get_comments_for_post(post_id):
    """
    Retrieves all comments for a specific post.

    @param post_id The ID of the post.
    @return A list of dictionaries containing comment text and author usernames.
    """
    db = get_db()
    return db.execute("""
        SELECT c.comment_text, u.username 
        FROM comments c 
        JOIN users u ON c.user_id = u.id 
        WHERE c.image_id = ?
    """, (post_id,)).fetchall()

def get_comments_for_post_paginated(post_id, limit=20, offset=0):
    """
    Retrieves a paginated list of comments for a specific post.

    @param post_id The ID of the post.
    @param limit The maximum number of comments to return (default 20).
    @param offset The number of comments to skip (default 0).
    @return A paginated list of comments.
    """
    db = get_db()
    comments = db.execute("""
       SELECT c.comment_text, u.username 
        FROM comments c 
        JOIN users u ON c.user_id = u.id 
        WHERE c.image_id = ?
        ORDER BY c.created_at DESC
        LIMIT ? OFFSET ?
    """, (post_id, limit, offset)).fetchall()
    
    return comments

def get_comments_count_for_post(post_id):
    db = get_db()
    count = db.execute("SELECT COUNT(*) as count FROM comments WHERE image_id = ?", (post_id,)).fetchone()
    return count["count"] if count else 0