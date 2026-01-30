from flask import Blueprint, request, jsonify
from flask import g
from app.middleware.auth import require_auth
from app.models.user import get_or_create_user
from app.models.comment import create_comment

bp = Blueprint('comments', __name__)

@bp.route('/comments', methods=['POST'])
@require_auth
def add_comment():
    user_id = get_or_create_user(g.user_claims['sub'])
    
    data = request.json
    create_comment(data['post_id'], user_id, data['text'])
    
    return jsonify({"message": "Comment added"}), 201