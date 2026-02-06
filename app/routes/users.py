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