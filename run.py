# run.py
import os
from app import create_app
from app.db.db import init_db

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