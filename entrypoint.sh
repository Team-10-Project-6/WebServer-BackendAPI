#!/bin/bash
# entrypoint.sh

# Run a quick python script to initialize the DB
python -c "from app.db.db import init_db; init_db()"

# Then start Gunicorn
exec gunicorn -w 2 -k gevent -b 0.0.0.0:5000 run:app