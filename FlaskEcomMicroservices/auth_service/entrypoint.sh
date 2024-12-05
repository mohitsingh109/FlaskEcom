#!/bin/sh

# Run migrations before starting the app
flask db upgrade

# Start the Flask app
exec python main.py
