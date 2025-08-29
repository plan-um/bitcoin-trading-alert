#!/bin/bash
# Railway startup script

# Set default port if not provided
if [ -z "$PORT" ]; then
    export PORT=5000
fi

echo "Starting app on port $PORT"

# Start gunicorn with the PORT
exec gunicorn app_simple:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --log-level info