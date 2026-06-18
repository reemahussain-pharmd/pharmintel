# File: streamlit_app.py (root)
# Purpose: Entry point for Streamlit Community Cloud deployment
# Connects to: frontend/app.py — this file simply imports and runs the main app
# Streamlit Cloud looks for this file at the root of the repo

import subprocess
import sys
import os

# When deployed on Streamlit Cloud, redirect to the frontend app
# Locally you can also run: streamlit run frontend/app.py

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, "-m", "streamlit", "run", "frontend/app.py"])
