const API = '';

const messagesEl = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const statusText = document.getElementById('statusText');
const clearBtn = document.getElementById('clearBtn');

let history = [];
let isLoading = false;

// ── Markdown renderer ─────────────────────────────────────────────────────────
function renderMarkdown(text) {
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/```[\w]*\n?([\s\S]*?)```/g, (_, c) => `<pre><code>${c.trim()}</code></pre>`)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^[\-\*] (.+)$/gm, '<li>$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    .replace(/^#{1,3} (.+)$/gm, '<strong>$1</strong>')
    .split('\n\n').map(p => p.trim() ? `<p>${p.replace(/\n/g, '<br>')}</p>` : '').join('');
}

// ── Messages ──────────────────────────────────────────────────────────────────
function appendMessage(role, content, meta = {}) {
  document.querySelector('.welcome')?.remove();

  const wrap = document.createElement('div');
  wrap.className = `message ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = role === 'user' ? 'U' : '🤖';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = renderMarkdown(content);

  if (role === 'bot' && meta.has_context) {
    const badge = document.createElement('div');
    badge.className = 'context-badge';
    badge.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg> Dựa trên ${meta.context_count} đoạn tài liệu`;
    bubble.appendChild(badge);
  }

  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showTyping() {
  const wrap = document.createElement('div');
  wrap.className = 'message bot typing';
  wrap.id = 'typing-indicator';
  wrap.innerHTML = `<div class="avatar">🤖</div><div class="bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>`;
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ── Send ──────────────────────────────────────────────────────────────────────
async function sendMessage() {
  const text = userInput.value.trim();
  if (!text || isLoading) return;

  isLoading = true;
  sendBtn.disabled = true;
  userInput.value = '';
  autoResize();

  appendMessage('user', text);
  showTyping();
  statusText.textContent = 'Đang xử lý...';

  history.push({ role: 'user', content: text });

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: history.slice(0, -1) }),
    });

    document.getElementById('typing-indicator')?.remove();

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Lỗi không xác định' }));
      appendMessage('bot', `⚠️ ${err.detail}`);
      history.pop();
    } else {
      const data = await res.json();
      appendMessage('bot', data.answer, { has_context: data.has_context, context_count: data.context_count });
      history.push({ role: 'assistant', content: data.answer });
    }
  } catch {
    document.getElementById('typing-indicator')?.remove();
    appendMessage('bot', '⚠️ Không thể kết nối đến server.');
    history.pop();
  }

  isLoading = false;
  sendBtn.disabled = false;
  statusText.textContent = 'Sẵn sàng trả lời';
  userInput.focus();
}

// ── Clear ─────────────────────────────────────────────────────────────────────
clearBtn.addEventListener('click', () => {
  if (!confirm('Xóa toàn bộ lịch sử chat?')) return;
  history = [];
  messagesEl.innerHTML = `
    <div class="welcome">
      <div class="welcome-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </div>
      <p>Xin chào! Tôi có thể giúp gì cho bạn?</p>
    </div>`;
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function autoResize() {
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 160) + 'px';
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
userInput.addEventListener('input', autoResize);
userInput.focus();
