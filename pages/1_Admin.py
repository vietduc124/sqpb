import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from rag import ingest_document, list_documents, delete_document, UPLOAD_DIR

load_dotenv(Path(__file__).parent.parent / ".env", override=True)

st.set_page_config(page_title="Admin – Tài liệu", page_icon="📁", layout="centered")

st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Authentication ────────────────────────────────────────────────────────────
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False

if not st.session_state.admin_auth:
    st.title("🔐 Đăng nhập Admin")
    with st.form("login_form"):
        pwd = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu...")
        submitted = st.form_submit_button("Đăng nhập", use_container_width=True)
        if submitted:
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("Sai mật khẩu!")
    st.stop()

# ── Admin UI ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns([5, 1])
with col1:
    st.title("📁 Quản lý tài liệu")
with col2:
    if st.button("Đăng xuất", use_container_width=True):
        st.session_state.admin_auth = False
        st.rerun()

# ── Upload ────────────────────────────────────────────────────────────────────
st.subheader("Tải tài liệu lên")

uploaded_files = st.file_uploader(
    "Chọn file",
    type=["pdf", "txt", "docx", "doc", "md"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded_files:
    for file in uploaded_files:
        dest = UPLOAD_DIR / file.name
        dest.write_bytes(file.getbuffer())
        with st.spinner(f"Đang xử lý **{file.name}**..."):
            chunks = ingest_document(dest, file.name)
        if chunks:
            st.success(f"✓ **{file.name}** — {chunks} đoạn văn bản")
        else:
            st.warning(f"⚠️ **{file.name}** — không đọc được nội dung")
    st.rerun()

st.divider()

# ── Document list ─────────────────────────────────────────────────────────────
st.subheader("Tài liệu trong cơ sở tri thức")

docs = list_documents()

if not docs:
    st.info("Chưa có tài liệu nào. Tải lên để bắt đầu.")
else:
    st.caption(f"{len(docs)} tài liệu · {sum(d['chunks'] for d in docs)} đoạn tổng cộng")
    st.markdown("")

    for doc in docs:
        col_name, col_chunks, col_btn = st.columns([5, 2, 1])
        with col_name:
            st.markdown(f"**{doc['name']}**")
        with col_chunks:
            st.caption(f"{doc['chunks']} đoạn")
        with col_btn:
            if st.button("🗑️", key=f"del_{doc['name']}", help=f"Xóa {doc['name']}"):
                with st.spinner("Đang xóa..."):
                    deleted = delete_document(doc["name"])
                st.toast(f"Đã xóa {doc['name']} ({deleted} đoạn)", icon="✅")
                st.rerun()
