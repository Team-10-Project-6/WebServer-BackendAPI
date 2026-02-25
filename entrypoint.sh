#!/bin/bash
# entrypoint.sh

# Initialize DB
python -c "from app.db.db import init_db; init_db()"

# Calculate workers: 1 per core is usually safe for heavy CPU tasks like Base64 decoding
# You can use 'nproc' to get CPU count
WORKERS=${GUNICORN_WORKERS:-$(nproc)}

echo "Starting Gunicorn with $WORKERS workers..."

exec gunicorn \
    --workers $WORKERS \
    --worker-class gevent \
    --worker-connections 1000 \
    --bind 0.0.0.0:5000 \
    run:app
