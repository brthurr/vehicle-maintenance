"""
run.py
------
Development entry point for the Vehicle Maintenance Tracker.

Usage
-----
    python run.py

Environment variables
---------------------
SECRET_KEY  : Flask secret key (default: dev-secret-change-in-production)
DB_PATH     : SQLite database file path (default: maintenance.db)
PORT        : Port to listen on (default: 5000)
"""

import os
from app import create_app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    upload_folder = os.path.join(os.path.dirname(__file__), "uploads")
    application = create_app(upload_folder=upload_folder)
    application.run(debug=True, host="0.0.0.0", port=port)
