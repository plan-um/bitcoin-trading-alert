#!/usr/bin/env bash
# Render start script

# Set default port if not provided
PORT=${PORT:-10000}

# Start the application with Gunicorn
exec gunicorn app_with_auth:app \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --workers 2 \
    --threads 4 \
    --worker-class sync \
    --log-level info \
    --access-logfile - \
    --error-logfile -