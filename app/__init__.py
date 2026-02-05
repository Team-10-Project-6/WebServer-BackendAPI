from flask import Flask
from flask_cors import CORS
from config import config

def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # CORS Configuration
    CORS(app, 
         resources={r"/api/*": {"origins": "*"}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # Initialize Auth0
    from app.middleware.auth import init_auth
    init_auth(app)
    
    # Register database teardown
    from app.db.db import close_db
    app.teardown_appcontext(close_db)
    
    # Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        from flask import jsonify
        return jsonify({"error": "Internal server error", "details": str(error)}), 500

    @app.errorhandler(401)
    def unauthorized(error):
        from flask import jsonify
        return jsonify({"error": "Unauthorized"}), 401
    
    # Register blueprints
    from app.routes import register_routes
    register_routes(app)
    
    return app