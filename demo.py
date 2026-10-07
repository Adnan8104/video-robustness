"""Local Streamlit entry point; launch with run.py demo."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from vidrobust.demo import main

main(ROOT)
