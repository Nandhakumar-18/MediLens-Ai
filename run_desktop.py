import sys
import os
import threading
import time
import webbrowser
from waitress import serve

# Add application directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database.db import Database

db = Database()

def open_browser():
    time.sleep(1.2)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    print("=======================================================")
    print("  MediLensAI Desktop App v2.0.0 — Standalone Offline   ")
    print("=======================================================")
    
    # 1. Initialize & Verify Database Integrity
    db.init_db()
    if db.verify_integrity():
        print("[SECURITY CHECK] Database integrity verified OK (100% Tamper-Free)")
    else:
        print("[WARNING] Database integrity check failed")

    # 2. Launch browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # 3. Serve production Waitress WSGI server
    print("Starting MediLensAI Desktop Engine on http://127.0.0.1:5000 ...")
    serve(app, host='127.0.0.1', port=5000)
