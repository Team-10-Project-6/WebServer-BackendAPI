from flask import Blueprint, request, jsonify, Response
from flask import g
from app.middleware.auth import require_auth
from app.models.user import get_or_create_user
from app.models.post import create_post, get_all_posts, get_post_by_id
from app.models.comment import get_comments_for_post

bp = Blueprint('posts', __name__)

@bp.route('/posts', methods=['GET', 'POST'])
@require_auth
def manage_posts():
    if request.method == 'POST':
        user_id = get_or_create_user(g.user_claims['sub'])
        
        file = request.files.get("image")
        description = request.form.get("description", "").strip()

        if not file:
            return jsonify({"error": "No image file provided"}), 400

        image_blob = file.read()
        create_post(user_id, file.filename, description, image_blob)
        
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
            "comments": [{"text": c["comment_text"], "author": c["username"]} for c in comment_rows]
        })
    
    return jsonify(results)

@bp.route('/images/download/<int:post_id>')
def serve_blob(post_id):
    row = get_post_by_id(post_id)
    if not row:
        return "Not Found", 404
    
    return Response(row["data"], mimetype='image/jpeg')