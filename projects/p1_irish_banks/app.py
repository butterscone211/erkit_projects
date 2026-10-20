"""Irish banks rate-path dashboard. Run:  streamlit run projects/p1_irish_banks/app.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import streamlit as st

dashboard = st.Page("pages/dashboard.py", title="Rate-path dashboard", icon=":material/tune:", default=True)
note = st.Page("pages/note.py", title="Research note", icon=":material/article:")
st.navigation([dashboard, note]).run()
