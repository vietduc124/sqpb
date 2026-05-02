from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

st.set_page_config(
    page_title="Trường Sĩ Quan Pháo Binh",
    page_icon="🎓",
    layout="wide",
)

pg = st.navigation(
    [
        st.Page("pages/chat.py", title="💬 Hỏi đáp", default=True),
        st.Page("pages/tac_gia.py", title="👥 Nhóm tác giả"),
    ],
    position="hidden",
)
pg.run()
