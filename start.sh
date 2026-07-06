#!/bin/bash
flask db upgrade
flask init-db
gunicorn app:app
