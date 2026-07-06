#!/bin/bash
set -e
echo "=== Starting deploy ==="
echo "Running migrations..."
python -m flask db upgrade
echo "Migrations done."
echo "Initializing database..."
python -m flask init-db
echo "Init done."
exec gunicorn --bind 0.0.0.0:$PORT app:app
