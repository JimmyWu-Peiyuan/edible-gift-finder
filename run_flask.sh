#!/bin/bash
# Run Flask app for Edible Gift Finder
cd "$(dirname "$0")"
./venv/bin/python -m flask --app flask_app run --port 5000
