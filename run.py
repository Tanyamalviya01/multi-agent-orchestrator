"""
run.py — One-command launcher for the AI Council Agent (no Docker needed).
Usage:
    python run.py
Starts both the FastAPI backend (port 8000) and Streamlit frontend (port 8501)
in parallel. Press Ctrl+C once to shut both down cleanly.
"""

import subprocess
import sys
import os
import signal
import time

# ─── SQLite fix — only needed on Linux ─────────────────────────────────────────
if sys.platform.startswith("linux"):
    try:
        __import__("pysqlite3")
        sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
    except ImportError:
        pass  # pysqlite3 not installed yet — installer will handle it

PYTHON = sys.executable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Fix ui.py to point at localhost instead of Docker service name
UI_FILE = os.path.join(BASE_DIR, "ui.py")
if os.path.exists(UI_FILE):
    with open(UI_FILE, "r") as f:
        content = f.read()
    # Replace Docker service hostname with localhost
    content = content.replace('BACKEND = "http://backend:8000"', 'BACKEND = "http://localhost:8000"')
    with open(UI_FILE, "w") as f:
        f.write(content)

print("=" * 60)
print("  AI Council Agent — Native Launcher")
print("=" * 60)
print()
print("Starting FastAPI backend on http://localhost:8000 ...")
backend = subprocess.Popen(
    [PYTHON, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=BASE_DIR,
)

time.sleep(2)  # Give backend a moment to boot

print("Starting Streamlit frontend on http://localhost:8501 ...")
frontend = subprocess.Popen(
    [PYTHON, "-m", "streamlit", "run", "ui.py",
     "--server.port", "8501",
     "--server.address", "0.0.0.0",
     "--server.headless", "true"],
    cwd=BASE_DIR,
)

print()
print("✅ Both services are running.")
print("   → Open http://localhost:8501 in your browser.")
print("   → Press Ctrl+C to stop everything.")
print()

def shutdown(sig, frame):
    print("\nShutting down...")
    frontend.terminate()
    backend.terminate()
    frontend.wait()
    backend.wait()
    print("Done. Goodbye!")
    sys.exit(0)

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

# Keep alive
backend.wait()
