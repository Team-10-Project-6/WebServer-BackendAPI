# app/routes/__init__.py
def register_routes(app):
    """Register all route blueprints"""
    from app.routes.health import bp as health_bp
    from app.routes.posts import bp as posts_bp
    from app.routes.comments import bp as comments_bp
    
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(posts_bp, url_prefix='/api')
    app.register_blueprint(comments_bp, url_prefix='/api')