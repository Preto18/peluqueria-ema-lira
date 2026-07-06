#!/bin/bash
set -e
python -m flask db upgrade
python -m flask init-db
exec gunicorn --bind 0.0.0.0:$PORT app:app
