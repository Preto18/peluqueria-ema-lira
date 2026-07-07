# tests/conftest.py
import sys
import os

# Usar SQLite para tests (no depender de DB externa)
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))