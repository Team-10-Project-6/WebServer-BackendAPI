from flask import Blueprint, request, jsonify
from flask import g
from app.middleware.auth import require_auth
from app.models.user import get_or_create_user
from app.models.post import get_post_by_id
from app.models.comment import create_comment, get_comments_for_post

bp = Blueprint('comments', __name__)

@bp.route('/comments', methods=['POST'])
@require_auth
def add_comment():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    post_id = data.get('post_id')
    text = data.get('text')
    
    # Validate required fields
    if not post_id:
        return jsonify({"error": "post_id is required"}), 400
    if not text or not text.strip():
        return jsonify({"error": "Comment text is required"}), 400
    
    try:
        user_id = get_or_create_user(g.user_claims['sub'])
        create_comment(post_id, user_id, text.strip())
        
        return jsonify( {"message": "Comment added"} ), 201
        
    except Exception as e:
        print(f"[ERROR]: Cannot create comment: {e}")
        return jsonify( {"error": "Failed to create comment"} ), 500
    
@bp.route('/comments/<int:post_id>', methods=['GET'])
def get_comments(post_id):
    post = get_post_by_id(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    comments_row = get_comments_for_post(post_id)
    comments = []
    for c in comments_row:
        comments.append({
            "text": c["comment_text"],
            "author": c["username"]
        })

    return jsonify(comments), 200