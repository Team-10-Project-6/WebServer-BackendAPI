# run.py
import os
from app import create_app
from app.db.db import init_db

app = create_app()

with app.app_context():
    init_db()

if __name__ == "__main__":
    print(f"[INFO] AUTH0_DOMAIN: {app.config['AUTH0_DOMAIN']}")
    host = "0.0.0.0" if os.path.exists("/.dockerenv") else "127.0.0.1"
    app.run(host=host, port=5000, debug=True)