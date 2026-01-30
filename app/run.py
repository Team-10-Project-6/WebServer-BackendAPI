import os
from flask import Flask
from flask_cors import CORS
from config import config
from utils.db import close_db, init_db
from middleware.auth import init_auth

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # CORS Configuration
    CORS(app, 
         resources={r"/api/*": {"origins": "*"}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # Initialize Auth0
    init_auth(app)
    
    # Register database teardown
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
    from routes import health, posts, comments
    
    app.register_blueprint(health.bp, url_prefix='/api')
    app.register_blueprint(posts.bp, url_prefix='/api')
    app.register_blueprint(comments.bp, url_prefix='/api')
    
    return app

if __name__ == "__main__":
    app = create_app()
    
    # Initialize database
    with app.app_context():
        init_db()
    
    print("[INFO] Starting Flask server...")
    print(f"[INFO] AUTH0_DOMAIN: {app.config['AUTH0_DOMAIN']}")
    print(f"[INFO] AUTH0_AUDIENCE: {app.config['AUTH0_AUDIENCE']}")
    
    host = "0.0.0.0" if os.path.exists("/.dockerenv") else "127.0.0.1"
    app.run(host=host, port=5000, debug=True)