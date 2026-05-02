import os
import re
import html
import base64
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
import anthropic
from rag import retrieve_context

load_dotenv(Path(__file__).parent.parent / ".env", override=True)

# ── Logo ───────────────────────────────────────────────────────────────────────
logo_path = Path(__file__).parent.parent / "assets" / "logo.jpg"
logo_html = '<div style="width:90px;height:90px;"></div>'
if logo_path.exists():
    b64 = base64.b64encode(logo_path.read_bytes()).decode()
    logo_html = f'<a href="/" target="_self"><img src="data:image/jpeg;base64,{b64}" style="height:90px;width:90px;object-fit:contain;cursor:pointer;" alt="Logo"/></a>'

# ── Markdown → HTML ────────────────────────────────────────────────────────────
def md(text: str) -> str:
    t = html.escape(text)
    t = re.sub(r'```(?:\w+)?\n(.*?)```', lambda m:
        f'<pre style="background:rgba(0,0,0,.08);padding:10px 14px;border-radius:6px;overflow-x:auto;margin:6px 0"><code>{m.group(1).strip()}</code></pre>',
        t, flags=re.DOTALL)
    t = re.sub(r'`([^`]+)`', r'<code style="background:rgba(0,0,0,.1);padding:1px 5px;border-radius:3px">\1</code>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
    t = re.sub(r'^#{1,3} (.+)$', r'<strong>\1</strong>', t, flags=re.MULTILINE)
    def to_ul(m):
        items = re.sub(r'^[-*] (.+)$', r'<li>\1</li>', m.group(0), flags=re.MULTILINE)
        return f'<ul style="padding-left:18px;margin:4px 0">{items}</ul>'
    t = re.sub(r'(^[-*] .+$\n?)+', to_ul, t, flags=re.MULTILINE)
    def to_ol(m):
        items = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', m.group(0), flags=re.MULTILINE)
        return f'<ol style="padding-left:18px;margin:4px 0">{items}</ol>'
    t = re.sub(r'(^\d+\. .+$\n?)+', to_ol, t, flags=re.MULTILINE)
    parts = t.split('\n\n')
    result = []
    for p in parts:
        p = p.strip()
        if not p: continue
        if p.startswith('<pre') or p.startswith('<ul') or p.startswith('<ol'):
            result.append(p)
        else:
            result.append(f'<p style="margin:0 0 6px">{p.replace(chr(10),"<br>")}</p>')
    return ''.join(result)

# ── CSS + Header + Ticker ──────────────────────────────────────────────────────
st.markdown(f"""
<style>
#MainMenu, footer, header {{ visibility:hidden; }}

.stApp {{ background:#f5edd8; }}
html,body,.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section.main,
.main .block-container,.block-container {{
    padding:0 !important; margin:0 !important;
    max-width:100% !important; width:100% !important;
}}

.pb-header {{
    display:flex; align-items:center; gap:24px;
    background:#fff; padding:14px 40px;
    border-bottom:2px solid #e0d0a0;
    box-shadow:0 2px 8px rgba(0,0,0,.06);
}}
.pb-title {{ flex:1; text-align:center; line-height:1.3; }}
.pb-title-1 {{ font-size:20px; font-weight:700; color:#1a5c1a; text-transform:uppercase; letter-spacing:1px; }}
.pb-title-2 {{ font-size:30px; font-weight:900; color:#c0392b; text-transform:uppercase; letter-spacing:2px; }}

.pb-ticker {{ background:#1a2e5a; padding:12px 20px; text-align:center; }}
.pb-ticker-inner {{ color:#ffd700; font-weight:700; font-size:15px; line-height:1.7; letter-spacing:.5px; }}

.pb-chat-bg {{
    position:fixed; top:50%; left:50%;
    transform:translate(-50%,-50%);
    width:min(500px,60vw); height:min(500px,60vw);
    pointer-events:none; z-index:0; opacity:.10;
    background:
        radial-gradient(circle,transparent 55px,#8b6914 56px,#8b6914 58px,transparent 59px),
        radial-gradient(circle,transparent 85px,#8b6914 86px,#8b6914 88px,transparent 89px),
        radial-gradient(circle,transparent 115px,#8b6914 116px,#8b6914 118px,transparent 119px),
        radial-gradient(circle,transparent 145px,#8b6914 146px,#8b6914 148px,transparent 149px),
        radial-gradient(circle,transparent 175px,#8b6914 176px,#8b6914 178px,transparent 179px),
        radial-gradient(circle,transparent 205px,#8b6914 206px,#8b6914 208px,transparent 209px),
        radial-gradient(circle at center,#8b6914 4px,transparent 5px);
    border-radius:50%;
}}

.pb-greeting {{ text-align:center; padding:56px 20px 20px; position:relative; z-index:1; }}
.pb-greeting-icon {{ font-size:80px; line-height:1; }}
.pb-greeting-text {{ font-size:21px; font-weight:700; color:#2c2c2c; margin-top:20px; line-height:1.5; }}

.chat-row {{ display:flex; padding:4px 24px; position:relative; z-index:1; }}
.chat-row.user {{ justify-content:flex-end; }}
.chat-row.bot  {{ justify-content:flex-start; }}
.bubble {{ max-width:68%; padding:10px 16px; font-size:14px; line-height:1.65; word-break:break-word; }}
.bubble.user {{ background:#1a5c1a; color:#fff; border-radius:18px 18px 4px 18px; }}
.bubble.bot {{ background:rgba(255,255,255,.92); color:#222; border-radius:18px 18px 18px 4px; border:1px solid #e0d0a0; }}
.bubble.bot code {{ background:rgba(0,0,0,.07); }}

[data-testid="stChatMessage"] {{ background:transparent !important; box-shadow:none !important; padding:4px 24px !important; }}

.pb-nav-btn {{
    display:inline-block; text-decoration:none;
    background:#1a2e5a; color:#ffd700 !important;
    border:2px solid #ffd700; border-radius:6px;
    padding:7px 16px; font-size:13px; font-weight:700; white-space:nowrap;
}}

@media(max-width:768px){{
    .pb-header{{ padding:10px 16px; gap:12px; }}
    .pb-header img{{ height:60px !important; width:60px !important; }}
    .pb-title-1{{ font-size:13px; }}
    .pb-title-2{{ font-size:18px; }}
    .bubble{{ max-width:85%; font-size:13px; }}
    .chat-row{{ padding:4px 12px; }}
    .pb-nav-btn{{ font-size:11px; padding:5px 10px; }}
}}
@media(max-width:480px){{
    .pb-title-1{{ font-size:11px; }}
    .pb-title-2{{ font-size:15px; }}
    .pb-header img{{ height:48px !important; width:48px !important; }}
}}
</style>

<div class="pb-header">
    {logo_html}
    <div class="pb-title">
        <div class="pb-title-1">Bộ Tư Lệnh Pháo Binh - Tên Lửa</div>
        <div class="pb-title-2">Trường Sĩ Quan Pháo Binh</div>
    </div>
    <a class="pb-nav-btn" href="/tac_gia" target="_self">👥 Nhóm tác giả</a>
</div>

<div class="pb-ticker">
    <span class="pb-ticker-inner">
        BÀI DỰ THI TÌM HIỂU 80 NĂM NGÀY TRUYỀN THỐNG BỘ ĐỘI PHÁO BINH - TÊN LỬA<br>
        QUÂN ĐỘI NHÂN DÂN VIỆT NAM<br>
        (1946 - 2026)
    </span>
</div>
<div class="pb-chat-bg"></div>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Greeting ───────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="pb-greeting">
        <div class="pb-greeting-icon">🎯</div>
        <div class="pb-greeting-text">
            Xin chào! Trường Sĩ quan Pháo binh<br>có thể giúp gì cho bạn?
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Lịch sử chat ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    side = "user" if msg["role"] == "user" else "bot"
    st.markdown(
        f'<div class="chat-row {side}"><div class="bubble {side}">{md(msg["content"])}</div></div>',
        unsafe_allow_html=True,
    )

# ── Chat input ─────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Hãy nhập câu hỏi của bạn tại đây..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(
        f'<div class="chat-row user"><div class="bubble user">{md(prompt)}</div></div>',
        unsafe_allow_html=True,
    )

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

    with st.chat_message("assistant"):
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
    st.rerun()
