#!/bin/sh
set -e

WORKERS="${GUNICORN_WORKERS:-5}"

if [ "${DEBUG:-false}" = "true" ]; then
    echo "Starting in DEBUG mode (hot reload enabled)"
    exec python -m src.app
else
    echo "Starting in PRODUCTION mode (gunicorn, $WORKERS workers)"
    exec gunicorn src.app:server -b 0.0.0.0:8050 -w "$WORKERS" --access-logfile - --error-logfile -
fi
