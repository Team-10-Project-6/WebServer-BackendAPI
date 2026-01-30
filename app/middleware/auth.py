import asyncio
from functools import wraps
from flask import request, jsonify, g, current_app
from auth0_api_python import ApiClient, ApiClientOptions
from auth0_api_python.errors import BaseAuthError

# Initialize Auth0 API client
api_client = None

def init_auth(app):
    global api_client
    api_client = ApiClient(ApiClientOptions(
        domain=app.config['AUTH0_DOMAIN'],
        audience=app.config['AUTH0_AUDIENCE']
    ))

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        
        print(f"[DEBUG] Auth header received: {auth_header[:50]}...")
        
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization header"}), 401
        
        token = auth_header.split(" ")[1]
        
        print(f"[DEBUG] Token segments: {len(token.split('.'))}")
        
        try:
            claims = asyncio.run(api_client.verify_access_token(token))
            g.user_claims = claims
            print(f"[DEBUG] Token verified successfully for user: {claims.get('sub')}")
            return f(*args, **kwargs)
        except BaseAuthError as e:
            print(f"[ERROR] Auth error: {str(e)}")
            return jsonify({"error": str(e)}), e.get_status_code()
        except Exception as e:
            print(f"[ERROR] Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Token validation failed", "details": str(e)}), 401
    
    return decorated_function