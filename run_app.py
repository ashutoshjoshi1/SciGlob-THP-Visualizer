import sys
import subprocess

try:
    print("Running main_gui.py............")
    subprocess.run([sys.executable, "main_gui.py"])
except Exception as e:
    print(f"Error : {e}")
