from flask import Blueprint, request, jsonify
from flask import g
from app.middleware.auth import require_auth
from app.models.user import get_or_create_user
from app.models.comment import create_comment

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