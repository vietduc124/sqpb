const API = '';

const fileInput = document.getElementById('fileInput');
const uploadZone = document.getElementById('uploadZone');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const uploadToast = document.getElementById('uploadToast');
const docGrid = document.getElementById('docGrid');
const docCount = document.getElementById('docCount');

// ── Drag & drop ───────────────────────────────────────────────────────────────
uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('dragover'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('dragover');
  handleFiles(Array.from(e.dataTransfer.files));
});
fileInput.addEventListener('change', () => handleFiles(Array.from(fileInput.files)));

// ── Upload ────────────────────────────────────────────────────────────────────
async function handleFiles(files) {
  if (!files.length) return;
  const allowed = new Set(['.pdf', '.txt', '.docx', '.doc', '.md']);
  const valid = files.filter(f => allowed.has('.' + f.name.split('.').pop().toLowerCase()));
  if (!valid.length) { showToast('Định dạng không hỗ trợ', 'error'); return; }

  uploadProgress.hidden = false;
  progressFill.style.width = '0%';

  const results = [];
  for (let i = 0; i < valid.length; i++) {
    const file = valid[i];
    progressFill.style.width = Math.round((i / valid.length) * 90) + '%';
    progressText.textContent = `Đang xử lý: ${file.name}`;

    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await fetch(`${API}/api/documents/upload`, { method: 'POST', body: fd });
      const data = await res.json();
      if (res.ok) results.push(`✓ ${file.name} (${data.chunks} đoạn)`);
      else results.push(`✗ ${file.name}: ${data.detail}`);
    } catch {
      results.push(`✗ ${file.name}: lỗi kết nối`);
    }
  }

  progressFill.style.width = '100%';
  progressText.textContent = 'Hoàn thành!';
  setTimeout(() => { uploadProgress.hidden = true; }, 1500);

  showToast(results.join('\n'), results.every(r => r.startsWith('✓')) ? 'success' : 'warn');
  fileInput.value = '';
  loadDocuments();
}

function showToast(msg, type = 'success') {
  uploadToast.textContent = msg;
  uploadToast.className = `upload-toast toast-${type}`;
  uploadToast.hidden = false;
  setTimeout(() => { uploadToast.hidden = true; }, 4000);
}

// ── Documents ─────────────────────────────────────────────────────────────────
async function loadDocuments() {
  try {
    const res = await fetch(`${API}/api/documents`);
    const docs = await res.json();
    renderDocs(docs);
  } catch {
    docGrid.innerHTML = '<p class="doc-error">Không thể tải danh sách tài liệu</p>';
  }
}

function renderDocs(docs) {
  docCount.textContent = `${docs.length} tài liệu`;
  if (!docs.length) {
    docGrid.innerHTML = `
      <div class="doc-empty">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <p>Chưa có tài liệu nào</p>
      </div>`;
    return;
  }

  const ext = name => name.split('.').pop().toLowerCase();
  const extColor = { pdf: '#ef5350', docx: '#1565c0', doc: '#1565c0', txt: '#4caf82', md: '#7c73ff' };

  docGrid.innerHTML = docs.map(d => `
    <div class="doc-card">
      <div class="doc-card-icon" style="background:${extColor[ext(d.name)] || '#7878a0'}22; color:${extColor[ext(d.name)] || '#7878a0'}">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <span class="doc-ext">.${ext(d.name)}</span>
      </div>
      <div class="doc-card-info">
        <div class="doc-card-name" title="${d.name}">${d.name}</div>
        <div class="doc-card-meta">${d.chunks} đoạn văn bản</div>
      </div>
      <button class="doc-card-delete" onclick="deleteDoc('${d.name}')" title="Xóa tài liệu">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"/>
          <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
        </svg>
      </button>
    </div>
  `).join('');
}

async function deleteDoc(name) {
  if (!confirm(`Xóa tài liệu "${name}" khỏi cơ sở tri thức?`)) return;
  try {
    await fetch(`${API}/api/documents/${encodeURIComponent(name)}`, { method: 'DELETE' });
    showToast(`Đã xóa: ${name}`, 'success');
    loadDocuments();
  } catch {
    showToast('Lỗi khi xóa', 'error');
  }
}

loadDocuments();
