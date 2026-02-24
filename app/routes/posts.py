from flask import Blueprint, request, jsonify, Response
from flask import g
from app.middleware.auth import require_auth
from app.models.user import get_or_create_user
from app.models.post import add_post, get_all_posts, get_post_by_id, get_posts_by_user_paginated, get_posts_paginated, update_post_description, update_post_image, delete_post
from app.models.comment import get_comments_for_post
import base64

bp = Blueprint('posts', __name__)

@bp.route('/posts', methods=['GET'])
def list_posts():
    """
    Endpoint: GET /posts
    
    Retrieves a paginated list of all posts, ordered by upload date descending.
    Each post includes its corresponding comments and metadata.
    
    @return JSON array of post objects.
    """
    # Get page from query params, default to 1
    page = request.args.get('page', default=1, type=int)
    limit = 20
    if page < 1: page = 1
    offset = (page - 1) * limit
    posts = get_posts_paginated(limit=limit, offset=offset)
    # posts = get_all_posts()
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

@bp.route('/posts/me', methods=['GET'])
@require_auth
def list_user_posts():
    """
    Endpoint: GET /posts/me
    
    Retrieves a paginated list of posts created by the authenticated user.
    Requires a valid JWT token.
    
    @return JSON array of the user's post objects.
    """
    # Get page from query params, default to 1
    page = request.args.get('page', default=1, type=int)
    limit = 20
    if page < 1: page = 1
    offset = (page - 1) * limit
    
    user_id = get_or_create_user(g.user_claims['sub'])
    
    # Use a paginated query for the specific user
    posts = get_posts_by_user_paginated(user_id, limit=limit, offset=offset) 
    
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
    """
    Endpoint: POST /posts
    
    Creates a new post with image data and description.
    Requires a valid JWT token.
    
    @return JSON indicating success or failure.
    """
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
    """
    Endpoint: PATCH /posts/<post_id>
    
    Updates an existing post's image or description.
    Users can only update their own posts.
    
    @param post_id The ID of the post to update.
    @return JSON object with success message and updated fields list.
    """
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
    """
    Endpoint: GET /posts/<post_id>
    
    Retrieves detailed information for a specific post.
    
    @param post_id The ID of the post to view.
    @return JSON object representing the post.
    """
    # Get a single post by ID
    row = get_post_by_id(post_id)

    if not row:
        return jsonify({"error": "Post not found"}), 404
    
    comments = get_comments_for_post(post_id)
    post = {
        "id": post_id,
        "description": row["description"],
        "username": row["username"], 
        "image_name": row["name"],
        "uploaded_at": row["uploaded_at"],
        "mime_type": row["mime_type"],
        "comments": len(comments),
        "base64_image": row["base64_image"]
    }
    
    return jsonify(post), 200

# route to remove a post
@bp.route('/posts/<int:post_id>', methods=['DELETE'])
@require_auth
def remove_post(post_id):
    """
    Endpoint: DELETE /posts/<post_id>
    
    Deletes a specific post. Users can only delete their own posts.
    Requires a valid JWT token.
    
    @param post_id The ID of the post to delete.
    @return JSON response indicating success or failure.
    """
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

# Add this route to posts.py
@bp.route('/posts/search', methods=['POST'])
def search_posts():
    """
    Endpoint: POST /posts/search
    
    Searches across all posts by comparing a query string to post descriptions and usernames.
    
    @return JSON list of matching posts.
    """
    data = request.json
    search_query = data.get('query', '').lower().strip()
    
    # Get all posts (or you could create a specific search function in your models)
    all_posts = get_all_posts()
    results = []
    
    for post in all_posts:
        # Filter posts by description or username
        if search_query in post["description"].lower() or search_query in post["username"].lower():
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
@bp.route('/images/download/<int:post_id>')
def serve_blob(post_id):
    """
    Endpoint: GET /images/download/<post_id>
    
    Serves the raw base64-decoded image blob directly as a binary response for a given post.
    
    @param post_id The ID of the post containing the image.
    @return A raw image response with the appropriate MIME type.
    """
    row = get_post_by_id(post_id)
    if not row:
        return "Not Found", 404
    
    return Response(base64.b64decode(row["base64_image"]), mimetype=row["mime_type"])
