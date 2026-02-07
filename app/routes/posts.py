from flask import Blueprint, request, jsonify, Response
from flask import g
from app.middleware.auth import require_auth
from app.models.user import get_or_create_user
from app.models.post import create_post, get_all_posts, get_post_by_id
from app.models.comment import get_comments_for_post
import base64

bp = Blueprint('posts', __name__)

@bp.route('/posts', methods=['GET', 'POST'])
@require_auth
def manage_posts():
    if request.method == 'POST':
        user_id = get_or_create_user(g.user_claims['sub'])
        data = request.json
        
        if not data.get('image'):
            return jsonify({"error": "No image data provided"}), 400
        
        # Decode base64 image
        try:
            image_blob = base64.b64decode(data['image'])
        except Exception as e:
            return jsonify({"error": "Invalid image data", "details": str(e)}), 400
        
        description = data.get("description", "").strip()
        filename = data.get("filename", "image.jpg")

        create_post(user_id, filename, description, image_blob)
        
        return jsonify({"message": "Post created successfully"}), 201

    # GET: Retrieve all posts
    post_rows = get_all_posts()
    
    results = []
    for post in post_rows:
        comment_rows = get_comments_for_post(post["id"])
        
        results.append({
            "id": post["id"],
            "description": post["description"],
            "username": post["username"],
            "comments": [{"text": c["comment_text"], "author": c["username"]} for c in comment_rows],
            "image_blob": base64.b64encode(post["data"]).decode('utf-8')  # Encode image blob as base64 string for frontend
        })
    
    return jsonify(results)

@bp.route('/images/download/<int:post_id>')
def serve_blob(post_id):
    row = get_post_by_id(post_id)
    if not row:
        return "Not Found", 404
    
    return Response(row["data"], mimetype='image/jpeg')