"""Local Streamlit entry point; launch with run.py demo."""
from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

mode = st.sidebar.radio("Mode", ["Check a video", "Prioritize for review"])
if mode == "Check a video":
    from vidrobust.demo import main
else:
    from vidrobust.review_demo import main

main(ROOT)
