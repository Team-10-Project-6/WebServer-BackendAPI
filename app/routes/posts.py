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
            "comments": len(comments),
            "mime_type": post["mime_type"],
            "base64_image": post["base64_image"]
        })
    
    return jsonify(results), 200

# TO DO: Image validation?
@bp.route('/posts', methods=['POST'])
@require_auth
def create_post():
    user_id = get_or_create_user(g.user_claims['sub'])
    data = request.json
    
    base64_image = data.get('image')
    description = data.get("description", "").strip()
    mime_type = data.get("mime_type")
    
    if not base64_image or not description or not mime_type:
        return jsonify({"error": "Missing image, description, or mime_type"}), 400
    
    # Validate filename
    filename = data.get("filename", "image.jpg")
    if len(filename) > 255:
        return jsonify({"error": "Filename too long"}), 400
    
    print(f'[INFO] Creating post for user ID: {user_id} with filename: {filename} and description: "{description}"', flush=True)
    
    # Store the base64 string directly in the database
    add_post(user_id, filename, description, base64_image, mime_type)
    
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
        mime_type = data.get('mime_type', "image/jpeg")

        update_post_image(post_id, data["image"], mime_type)
        updated_fields.append("image")

    # Update post description if provided
    if data.get("description") is not None:
        new_description = data["description"].strip()
        if not new_description:
            return jsonify({"error": "Description cannot be empty"}), 400
        
        update_post_description(post_id, new_description)
        updated_fields.append("description")

    if not updated_fields:
        return jsonify({"error": "No valid fields to update"}), 400

    return jsonify({"message": "Post updated successfully", "updated_fields": updated_fields}), 200

@bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    # Get a single post by ID
    row = get_post_by_id(post_id)

    if not row:
        return jsonify({"error": "Post not found"}), 404
    
    post = {
        "description": row["description"],
        "username": row["name"],  
        "uploaded_at": row["uploaded_at"],
        "mime_type": row["mime_type"],
        "base64_image": row["base64_image"]
    }
    
    return jsonify(post), 200

@bp.route('/posts/<int:post_id>/comments', methods=['GET'])
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

@bp.route('/images/download/<int:post_id>')
def serve_blob(post_id):
    row = get_post_by_id(post_id)
    if not row:
        return "Not Found", 404
    
    return Response(base64.b64decode(row["base64_image"]), mimetype=row["mime_type"])