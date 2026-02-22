from jose import jwt, jwk
from jose.exceptions import JWTError, ExpiredSignatureError
import requests
import time as _time
from functools import wraps
from flask import request, jsonify, g, current_app

# ---------------------------------------------------------------------------
# JWKS cache — module-level dict persists for the lifetime of the worker process
# ---------------------------------------------------------------------------
_jwks_cache = {"keys": None, "fetched_at": 0.0}
_JWKS_TTL = 3600  # seconds — re-fetch once per hour

def _get_jwks(domain):
    now = _time.monotonic()
    if _jwks_cache["keys"] is None or (now - _jwks_cache["fetched_at"]) > _JWKS_TTL:
        print(f"[AUTH] Fetching JWKS from Auth0 for domain: {domain}", flush=True)
        resp = requests.get(
            f"https://{domain}/.well-known/jwks.json",
            timeout=10
        )
        resp.raise_for_status()
        _jwks_cache["keys"] = resp.json()
        _jwks_cache["fetched_at"] = now
        print(f"[AUTH] JWKS cached successfully ({len(_jwks_cache['keys']['keys'])} keys)", flush=True)
    return _jwks_cache["keys"]

def _get_signing_key(domain, token):
    jwks = _get_jwks(domain)
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    for key in jwks["keys"]:
        if key["kid"] == kid:
            return jwk.construct(key)
    # kid not found — cache may be stale, force refresh once
    print(f"[AUTH] kid {kid!r} not found in cache, forcing refresh", flush=True)
    _jwks_cache["fetched_at"] = 0.0
    jwks = _get_jwks(domain)
    for key in jwks["keys"]:
        if key["kid"] == kid:
            return jwk.construct(key)
    raise Exception(f"Unable to find signing key for kid: {kid!r}")

def init_auth(app):
    """Pre-warm the JWKS cache at worker startup."""
    try:
        _get_jwks(app.config["AUTH0_DOMAIN"])
        print("[AUTH] JWKS pre-warmed successfully", flush=True)
    except Exception as e:
        print(f"[AUTH] WARNING: Could not pre-fetch JWKS at startup: {e}", flush=True)

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(" ")[1]

        try:
            domain   = current_app.config["AUTH0_DOMAIN"]
            audience = current_app.config["AUTH0_AUDIENCE"]

            signing_key = _get_signing_key(domain, token)

            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=audience,
                issuer=f"https://{domain}/",
            )

            g.user_claims = claims
            return f(*args, **kwargs)

        except ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except JWTError as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Token validation failed", "details": str(e)}), 401

    return decorated_function