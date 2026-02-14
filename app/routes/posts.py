from flask import Blueprint, request, jsonify, Response
from flask import g
from app.middleware.auth import require_auth
from app.models.user import get_or_create_user
from app.models.post import add_post, get_all_posts, get_post_by_id, update_post_description, update_post_image, delete_post
from app.models.comment import get_comments_for_post
import base64

bp = Blueprint('posts', __name__)

@bp.route('/posts', methods=['GET'])
def list_posts():
    # GET: Retrieve all posts and comments
    posts = get_all_posts()
    results = []
    
    for post in posts:
        comments = get_comments_for_post(post["id"])
        results.append({
            "id": post["id"],
            "description": post["description"],
            "username": post["username"],
            "uploaded_at": post["uploaded_at"],
            "comments": [{"text": c["comment_text"], "author": c["username"]} for c in comments],
            "mime_type": post["mime_type"],
            "image_blob": base64.b64encode(post["data"]).decode('utf-8')  # Encode image blob as base64 string for frontend
        })
    
    return jsonify(results), 200

@bp.route('/posts', methods=['POST'])
@require_auth
def create_post():
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
    mime_type = data.get('mime_type', "image/jpeg")

    print(f'[INFO] Creating post for user ID: {user_id} with filename: {filename} and description: "{description}"', flush=True)
    add_post(user_id, filename, description, image_blob, mime_type)
    
    return jsonify({"message": "Post created successfully"}), 201

@bp.route('/posts/<int:post_id>', methods=['PATCH'])
@require_auth
def update_post(post_id):
    user_id = get_or_create_user(g.user_claims['sub'])
    data = request.json

    # Check if post exists and belongs to user
    post = get_post_by_id(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    
    if post["user_id"] != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    updated_fields = []

    # Update post image if new image data is provided
    if data.get("image"):
        image_blob = base64.b64decode(data["image"])
        mime_type = data.get('mime_type', "image/jpeg")
        update_post_image(post_id, image_blob, mime_type)
        updated_fields.append("image")

    # Update post description if provided
    if data.get("description"):
        new_description = data["description"].strip()
        update_post_description(post_id, new_description)
        updated_fields.append("description")

    return jsonify({"message": "Post updated successfully", "updated_fields": updated_fields}), 200

@bp.route('/images/download/<int:post_id>')
def serve_blob(post_id):
    row = get_post_by_id(post_id)
    if not row:
        return "Not Found", 404
    
    return Response(row["data"], mimetype=row["mime_type"])

# route to remove a post
@bp.route('/posts/<int:post_id>', methods=['DELETE'])
@require_auth
def remove_post(post_id):
    # obtains user id from auth token
    user_id = get_or_create_user(g.user_claims['sub'])
    post = get_post_by_id(post_id)

    if not post:
        return jsonify({"error": "Post not found"}), 404
    
    if post["user_id"] != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    if delete_post(post_id, user_id):
        return jsonify({"message": "Post deleted successfully"}), 200
    
    return jsonify({"error": "Post not found or unauthorized"}), 404