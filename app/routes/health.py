from flask import Blueprint, jsonify
from app.middleware.auth import require_auth
from flask import g

bp = Blueprint('health', __name__)

@bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Server is running"})

@bp.route('/foobar', methods=['GET'])
@require_auth
def foobar():
    try:
        return jsonify({
            "message": "GET SUCCESSFUL", 
            "blah": ["this", "is", "explained"],
            "user": {
                "sub": g.user_claims.get('sub'),
                "email": g.user_claims.get('email'),
                "all_claims": g.user_claims
            }
        })
    except Exception as e:
        print(f"[ERROR] In foobar endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500