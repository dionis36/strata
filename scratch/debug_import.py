import sys
import os

# Add current directory to path
sys.path.append("/home/dio/Documents/strata/frontend")

try:
    from views.modernization_decision_engine import show_modernization_decision_engine
    print("SUCCESS: Module imported correctly.")
except ImportError as e:
    print(f"FAILURE: {e}")
    # List files to debug
    print("Files in views/:")
    print(os.listdir("/home/dio/Documents/strata/frontend/views"))
