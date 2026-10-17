"""Everything this companion claims, in one command.

    python run_all.py
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    sys.exit(subprocess.run([sys.executable, str(HERE / "the_crowd_and_the_chain.py")], cwd=HERE).returncode)
