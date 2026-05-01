import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
import anthropic
from rag import retrieve_context

load_dotenv(Path(__file__).parent / ".env", override=True)

st.set_page_config(page_title="Trợ lý AI", page_icon="💬", layout="centered")

st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
/* Ẩn trang Admin khỏi sidebar */
[data-testid="stSidebarNavItems"] li:has(a[href$="admin"]) {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

st.title("💬 Trợ lý AI")

USER_AVATAR = "https://api.dicebear.com/9.x/avataaars/svg?seed=user&backgroundColor=b6e3f4&top=shortHair"
BOT_AVATAR  = "https://api.dicebear.com/9.x/bottts/svg?seed=claude&backgroundColor=d1d4f9"

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    avatar = USER_AVATAR if msg["role"] == "user" else BOT_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if prompt := st.chat_input("Nhập câu hỏi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    context_chunks = retrieve_context(prompt)

    if context_chunks:
        context_text = "\n\n---\n\n".join(context_chunks)
        system_prompt = (
            "Bạn là trợ lý hỏi đáp. Chỉ được trả lời dựa trên nội dung tài liệu được cung cấp bên dưới. "
            "Tuyệt đối không được bịa đặt, suy đoán hoặc dùng kiến thức bên ngoài tài liệu. "
            "Nếu tài liệu không có thông tin để trả lời câu hỏi, hãy nói rõ: "
            "\"Tôi không tìm thấy thông tin này trong tài liệu được cung cấp.\"\n\n"
            f"### Nội dung tài liệu:\n{context_text}"
        )
    else:
        system_prompt = (
            "Bạn là trợ lý hỏi đáp. Hiện chưa có tài liệu nào trong cơ sở tri thức. "
            "Hãy thông báo cho người dùng biết và đề nghị họ tải tài liệu lên trang Admin trước khi đặt câu hỏi. "
            "Không được tự trả lời bằng kiến thức bên ngoài."
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
