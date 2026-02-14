<<<<<<< HEAD
from flask import Blueprint, request, jsonify
from flask import g
from app.middleware.auth import require_auth
from app.models.user import get_or_create_user
from app.models.comment import create_comment
from app.db.db import get_db

bp = Blueprint('users', __name__)
# This would be for the user which is calling for their own profile. this is not complete.
@bp.route("/profile", methods=["GET"])
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
    }), 200
=======
from flask import Blueprint, request, jsonify, g
from app.middleware.auth import require_auth
from app.models.user import get_or_create_user, update_username

bp = Blueprint('users', __name__)

@bp.route('/user/username', methods=['PUT'])
@require_auth
def update_user_username():
    # get user id from auth token
    print(f'[INFO] Received request to update username. User claims: {g.user_claims}', flush=True)
    user_id = get_or_create_user(g.user_claims['sub'])

    data = request.json
    if not data or 'username' not in data:
        return jsonify({"error": "Username is required"}), 400
        
    new_username = data['username'].strip()
    
    # simple validation
    if len(new_username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
        
    print(f'[INFO] Attempting to update username for user ID {user_id} to "{new_username}"', flush=True)

    if update_username(user_id, new_username):
        return jsonify({"message": "Username updated successfully", "username": new_username}), 200
    else:
        return jsonify({"error": "Username is already taken"}), 409
>>>>>>> origin/main
