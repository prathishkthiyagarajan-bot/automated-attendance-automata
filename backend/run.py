"""
Runner script for Render when Root Directory is set to 'backend'.
"""
import os
import sys
from dotenv import load_dotenv

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(PROJECT_DIR, ".env"))

from database import Database
from seed_data import seed_all
from app import app

def main():
    port = int(os.environ.get("PORT", 5000))
    print("[RUNNER] Initializing Database Engine...")
    Database.init_database()
    seed_all()
    print(f"[RUNNER] Starting Attendance System on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    main()
