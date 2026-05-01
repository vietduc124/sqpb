import os
import base64
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
import anthropic
from rag import retrieve_context

load_dotenv(Path(__file__).parent / ".env", override=True)

st.set_page_config(
    page_title="Trường Sĩ Quan Pháo Binh",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Logo
logo_path = Path(__file__).parent / "assets" / "logo.png"
logo_html = '<div style="width:90px;height:90px;"></div>'
if logo_path.exists():
    b64 = base64.b64encode(logo_path.read_bytes()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64}" style="height:90px;width:90px;object-fit:contain;" alt="Logo"/>'

st.markdown(f"""
<style>
/* ── Ẩn sidebar & chrome ── */
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {{ display: none !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}

/* ── Layout ── */
.stApp {{ background: #f5edd8; }}
.main .block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}

/* ── Header ── */
.pb-header {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 24px;
    background: #ffffff;
    padding: 14px 40px;
    border-bottom: 2px solid #e0d0a0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}}
.pb-title {{ text-align: center; line-height: 1.3; }}
.pb-title-1 {{
    font-size: 20px; font-weight: 700;
    color: #1a5c1a; text-transform: uppercase; letter-spacing: 1px;
}}
.pb-title-2 {{
    font-size: 30px; font-weight: 900;
    color: #c0392b; text-transform: uppercase; letter-spacing: 2px;
}}

/* ── Ticker ── */
.pb-ticker {{
    background: #1a2e5a;
    padding: 9px 0;
    overflow: hidden;
    white-space: nowrap;
}}
.pb-ticker-inner {{
    display: inline-block;
    animation: marquee 40s linear infinite;
    color: #ffd700;
    font-weight: 600;
    font-size: 14px;
    padding-left: 100%;
}}
@keyframes marquee {{
    from {{ transform: translateX(0%);    }}
    to   {{ transform: translateX(-100%); }}
}}

/* ── Watermark background ── */
.pb-chat-bg {{
    position: fixed;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: min(500px, 60vw);
    height: min(500px, 60vw);
    pointer-events: none;
    z-index: 0;
    opacity: 0.10;
    background:
        radial-gradient(circle, transparent  55px, #8b6914  56px, #8b6914  58px, transparent  59px),
        radial-gradient(circle, transparent  85px, #8b6914  86px, #8b6914  88px, transparent  89px),
        radial-gradient(circle, transparent 115px, #8b6914 116px, #8b6914 118px, transparent 119px),
        radial-gradient(circle, transparent 145px, #8b6914 146px, #8b6914 148px, transparent 149px),
        radial-gradient(circle, transparent 175px, #8b6914 176px, #8b6914 178px, transparent 179px),
        radial-gradient(circle, transparent 205px, #8b6914 206px, #8b6914 208px, transparent 209px),
        radial-gradient(circle, transparent 235px, #8b6914 236px, #8b6914 238px, transparent 239px),
        radial-gradient(circle at center, #8b6914 4px, transparent 5px);
    border-radius: 50%;
}}

/* ── Greeting ── */
.pb-greeting {{
    text-align: center;
    padding: 56px 20px 20px;
    position: relative;
    z-index: 1;
}}
.pb-greeting-icon {{ font-size: 80px; line-height: 1; }}
.pb-greeting-text {{
    font-size: 21px; font-weight: 700; color: #2c2c2c;
    margin-top: 20px; line-height: 1.5;
}}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {{
    background: rgba(255,255,255,0.88) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(4px);
    position: relative;
    z-index: 1;
}}

/* ── Input ── */
[data-testid="stChatInputContainer"] {{
    background: rgba(255,255,255,0.95) !important;
    border-top: 1px solid #ddd;
    padding: 10px 16px !important;
    position: relative; z-index: 2;
}}
[data-testid="stChatInput"] textarea {{
    font-size: 15px !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{
    color: #aaa !important;
}}

/* ── Responsive ── */
@media (max-width: 768px) {{
    .pb-header {{ padding: 10px 16px; gap: 12px; }}
    .pb-header img {{ height: 60px !important; width: 60px !important; }}
    .pb-title-1 {{ font-size: 13px; letter-spacing: 0; }}
    .pb-title-2 {{ font-size: 18px; letter-spacing: 0.5px; }}
    .pb-ticker-inner {{ font-size: 12px; }}
    .pb-greeting {{ padding: 32px 16px 16px; }}
    .pb-greeting-icon {{ font-size: 56px; }}
    .pb-greeting-text {{ font-size: 16px; }}
    .pb-chat-bg {{ width: 80vw; height: 80vw; }}
}}
@media (max-width: 480px) {{
    .pb-title-1 {{ font-size: 11px; }}
    .pb-title-2 {{ font-size: 15px; }}
    .pb-header img {{ height: 48px !important; width: 48px !important; }}
}}
</style>

<!-- Header -->
<div class="pb-header">
    {logo_html}
    <div class="pb-title">
        <div class="pb-title-1">Bộ Tư Lệnh Pháo Binh - Tên Lửa</div>
        <div class="pb-title-2">Trường Sĩ Quan Pháo Binh</div>
    </div>
</div>

<!-- Ticker -->
<div class="pb-ticker">
    <span class="pb-ticker-inner">
        📢&nbsp; Cuộc thi tìm hiểu 80 năm truyền thống Bộ tổng tham mưu (07/9/1945 - 07/9/2025)
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        📢&nbsp; Cuộc thi tìm hiểu 80 năm truyền thống Bộ tổng tham mưu (07/9/1945 - 07/9/2025)
    </span>
</div>

<!-- Watermark -->
<div class="pb-chat-bg"></div>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
USER_AVATAR = "https://api.dicebear.com/9.x/avataaars/svg?seed=user&backgroundColor=b6e3f4&top=shortHair"
BOT_AVATAR  = "https://api.dicebear.com/9.x/bottts/svg?seed=claude&backgroundColor=d1d4f9"

if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Greeting (khi chưa có tin nhắn) ───────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="pb-greeting">
        <div class="pb-greeting-icon">🎯</div>
        <div class="pb-greeting-text">
            Xin chào! Trường Sĩ quan Pháo binh<br>có thể giúp gì cho bạn?
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Hiển thị lịch sử chat ─────────────────────────────────────────────────────
for msg in st.session_state.messages:
    avatar = USER_AVATAR if msg["role"] == "user" else BOT_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Hãy nhập câu hỏi của bạn tại đây..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    context_chunks = retrieve_context(prompt)

    if context_chunks:
        context_text = "\n\n---\n\n".join(context_chunks)
        system_prompt = (
            "Bạn là trợ lý hỏi đáp của Trường Sĩ Quan Pháo Binh. "
            "Chỉ được trả lời dựa trên nội dung tài liệu được cung cấp bên dưới. "
            "Tuyệt đối không được bịa đặt, suy đoán hoặc dùng kiến thức bên ngoài tài liệu. "
            "Nếu tài liệu không có thông tin để trả lời, hãy nói rõ: "
            "\"Tôi không tìm thấy thông tin này trong tài liệu được cung cấp.\"\n\n"
            f"### Nội dung tài liệu:\n{context_text}"
        )
    else:
        system_prompt = (
            "Bạn là trợ lý hỏi đáp của Trường Sĩ Quan Pháo Binh. "
            "Hiện chưa có tài liệu nào trong cơ sở tri thức. "
            "Hãy thông báo cho người dùng và đề nghị liên hệ admin để tải tài liệu lên."
        )

    api_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        def stream_response():
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=system_prompt,
                messages=api_messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        response = st.write_stream(stream_response())
        if context_chunks:
            st.caption(f"📎 Dựa trên {len(context_chunks)} đoạn tài liệu")

    st.session_state.messages.append({"role": "assistant", "content": response})
