"""
Automated Attendance Management System Using Finite Automata
Startup & Runner Script
"""

import os
import sys
import webbrowser
import threading
import time
from dotenv import load_dotenv

# Ensure backend directory is in sys.path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

# Load .env
load_dotenv(os.path.join(PROJECT_DIR, ".env"))

from mongo_db import MONGO_URI
from database import Database
from seed_data import seed_all
from app import app

def open_browser(port):
    time.sleep(1.2)
    url = f"http://127.0.0.1:{port}"
    print(f"[RUNNER] Opening browser at {url} ...")
    webbrowser.open(url)

def main():
    port = int(os.environ.get("PORT", 5000))

    # Initialize and seed database if not already done
    print("[RUNNER] Initializing Database Engine...")
    Database.init_database()
    seed_all()

    active_db = Database.get_active_engine().upper()
    mongo_target = MONGO_URI.split("@")[-1] if "@" in MONGO_URI else MONGO_URI

    banner = f"""
================================================================================
       AUTOMATED ATTENDANCE MANAGEMENT SYSTEM USING FINITE AUTOMATA (DFA)
================================================================================
  Server URL:        http://127.0.0.1:{port}
  Active Database:   {active_db}
  MongoDB URI:       {mongo_target}
  
  DEMO LOGIN CREDENTIALS:
  ------------------------------------------------------------------------------
  1. System Administrator:
     Email:    admin@college.edu
     Password: admin123
     Role:     Administrator (Full access, DFA Visualizer, Admin Reset S4 -> S0)

  2. Faculty (Computer Science & Engineering):
     Email:    faculty1@college.edu
     Password: faculty123
     Role:     Faculty (Prof. Grace Hopper, CS301 - Theory of Computation)

  3. Faculty (Electronics & Communication):
     Email:    faculty3@college.edu
     Password: faculty123
     Role:     Faculty (Prof. Claude Shannon, EC301 - DSP)

  4. Student (Satisfactory Attendance ~90%):
     Email:    student1@college.edu
     Password: student123
     Role:     Student (Alice Walker, 2024CSE001)

  5. Student (Critical Warning Attendance < 75%):
     Email:    student8@college.edu
     Password: student123
     Role:     Student (Hannah Abbott, 2024CSE008 - Triggers <75% Warning!)
================================================================================
"""
    print(banner)

    # Launch browser in a background daemon thread
    if not os.environ.get("NO_BROWSER"):
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    main()
