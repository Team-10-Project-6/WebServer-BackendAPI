import asyncio
from functools import wraps
from flask import Flask, request, jsonify, session, Response
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
app.secret_key = "dev-secret"

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

# User authentication
@app.route("/api/login", methods=["POST"])
def login():
    username = request.json.get("username", "").strip()
    if not username:
        return jsonify({"error": "Username is required"}), 400

    db = get_db()
    user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()

    if user is None:
        db.execute("INSERT INTO users (username) VALUES (?)", (username,))
        db.commit()
        user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()

    session["username"] = username
    session["user_id"] = user["id"]
    return jsonify({"message": "Login successful", "user_id": user["id"], "username": username})

# Post management with BLOB storage
@app.route("/api/posts", methods=["GET", "POST"])
@require_auth
def manage_posts():
    db = get_db()

    if request.method == "POST":
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        
        file = request.files.get("image")
        description = request.form.get("description", "").strip()

        if not file:
            return jsonify({"error": "No image file provided"}), 400

        # Read file as binary for BLOB storage
        image_blob = file.read()

        db.execute(
            "INSERT INTO images (user_id, name, description, data, uploaded_at) VALUES (?, ?, ?, ?, ?)",
            (session.get("user_id"), file.filename, description, image_blob, int(time.time()))
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

# Serve image BLOBs
@app.route("/api/images/download/<int:post_id>")
def serve_blob(post_id):
    db = get_db()
    row = db.execute("SELECT data, name FROM images WHERE id = ?", (post_id,)).fetchone()
    if not row:
        return "Not Found", 404
    
    return Response(row["data"], mimetype='image/jpeg')

# Comment management
@app.route("/api/comments", methods=["POST"])
def add_comment():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    db = get_db()
    db.execute(
        "INSERT INTO comments (image_id, user_id, comment_text, created_at) VALUES (?, ?, ?, ?)",
        (data['post_id'], session['user_id'], data['text'], int(time.time()))
    )
    db.commit()
    return jsonify({"message": "Comment added"}), 201

@app.route("/api/foobar", methods=["GET"])
def foobar():
    return jsonify({"message": "GET SUCCESSFUL", "blah" : ["this", "is", "explained"]})

# Database initialization
if __name__ == "__main__":
    with get_db() as db:
        db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE)")
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