import asyncio
from functools import wraps
from flask import Flask, request, jsonify, g, Response
import sqlite3
import os
import time
from flask_cors import CORS
from dotenv import load_dotenv
from auth0_api_python import ApiClient, ApiClientOptions
from auth0_api_python.errors import BaseAuthError

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

# Initialize Auth0 API client (singleton - created once)
api_client = ApiClient(ApiClientOptions(
    domain=os.getenv("AUTH0_DOMAIN"),
    audience=os.getenv("AUTH0_AUDIENCE")
))

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization header"}), 401
        
        token = auth_header.split(" ")[1]
        
        try:
            claims = asyncio.run(api_client.verify_access_token(token))
            g.user_claims = claims
            return f(*args, **kwargs)
        except BaseAuthError as e:
            return (
                jsonify({"error": str(e)}),
                e.get_status_code(),
                e.get_headers()
            )
    
    return decorated_function

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def get_or_create_user(auth0_sub):
    """Get or create user based on Auth0 subject identifier"""
    db = get_db()
    user = db.execute("SELECT id, username FROM users WHERE auth0_sub = ?", (auth0_sub,)).fetchone()
    
    if user is None:
        # Extract email or username from claims if available
        email = g.user_claims.get('email', f'user_{auth0_sub[:9]}')
        print(f'[INFO] Creating new user with email: {email}')
        print(email)
        db.execute("INSERT INTO users (auth0_sub, username) VALUES (?, ?)", (auth0_sub, email))
        db.commit()
        user = db.execute("SELECT id, username FROM users WHERE auth0_sub = ?", (auth0_sub,)).fetchone()
        
    return user["id"]

# Post management with BLOB storage
@app.route("/api/posts", methods=["GET", "POST"])
@require_auth
def manage_posts():
    db = get_db()

    if request.method == "POST":
        # Get user_id from Auth0 claims instead of session
        user_id = get_or_create_user(g.user_claims['sub'])
        
        file = request.files.get("image")
        description = request.form.get("description", "").strip()

        if not file:
            return jsonify({"error": "No image file provided"}), 400

        # Read file as binary for BLOB storage
        image_blob = file.read()

        db.execute(
            "INSERT INTO images (user_id, name, description, data, uploaded_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, file.filename, description, image_blob, int(time.time()))
        )
        db.commit()
        return jsonify({"message": "Post created successfully with BLOB"}), 201

    # GET: Retrieve all posts and their comments
    post_rows = db.execute("""
        SELECT i.id, i.description, i.uploaded_at, u.username 
        FROM images i JOIN users u ON i.user_id = u.id 
        ORDER BY i.uploaded_at DESC
    """).fetchall()

    results = []
    for post in post_rows:
        comment_rows = db.execute("""
            SELECT c.comment_text, u.username FROM comments c 
            JOIN users u ON c.user_id = u.id WHERE c.image_id = ?
        """, (post["id"],)).fetchall()

        results.append({
            "id": post["id"],
            "description": post["description"],
            "username": post["username"],
            "comments": [{"text": c["comment_text"], "author": c["username"]} for c in comment_rows]
        })
    return jsonify(results)

# Serve image BLOBs - can be public or protected depending on your needs
@app.route("/api/images/download/<int:post_id>")
def serve_blob(post_id):
    db = get_db()
    row = db.execute("SELECT data, name FROM images WHERE id = ?", (post_id,)).fetchone()
    if not row:
        return "Not Found", 404
    
    return Response(row["data"], mimetype='image/jpeg')

# Comment management
@app.route("/api/comments", methods=["POST"])
@require_auth
def add_comment():
    # Get user_id from Auth0 claims instead of session
    user_id = get_or_create_user(g.user_claims['sub'])
    
    data = request.json
    db = get_db()
    db.execute(
        "INSERT INTO comments (image_id, user_id, comment_text, created_at) VALUES (?, ?, ?, ?)",
        (data['post_id'], user_id, data['text'], int(time.time()))
    )
    db.commit()
    return jsonify({"message": "Comment added"}), 201

@app.route("/api/foobar", methods=["GET"])
@require_auth
def foobar():
    auth_header = request.headers.get("Authorization", "")
    print(f"Auth header: {auth_header}")
    print(f"Token segments: {len(auth_header.split('.'))}")
    return jsonify({
        "message": "GET SUCCESSFUL", 
        "blah": ["this", "is", "explained"],
        "user_info": {
            "sub": g.user_claims.get('sub'),
            "email": g.user_claims.get('email'),
            "all_claims": g.user_claims
        }
    })

# Optional: User info endpoint
@app.route("/api/user/me", methods=["GET"])
@require_auth
def get_current_user():
    user_id = get_or_create_user(g.user_claims['sub'])
    db = get_db()
    user = db.execute("SELECT id, username, auth0_sub FROM users WHERE id = ?", (user_id,)).fetchone()
    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "auth0_sub": user["auth0_sub"],
        "email": g.user_claims.get('email')
    })

# Database initialization
if __name__ == "__main__":
    with get_db() as db:
        # Update users table to include auth0_sub
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, 
                username TEXT UNIQUE,
                auth0_sub TEXT UNIQUE
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, 
                description TEXT, data BLOB, uploaded_at INTEGER, updated_at INTEGER
            )""")
        db.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY, image_id INTEGER, user_id INTEGER, 
                comment_text TEXT, created_at INTEGER,
                FOREIGN KEY(image_id) REFERENCES images(id)
            )""")
    
    host = "0.0.0.0" if os.path.exists("/.dockerenv") else "127.0.0.1"
    app.run(host=host, port=5000, debug=True)