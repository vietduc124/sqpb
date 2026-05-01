import os
import shutil
from pathlib import Path
from typing import List

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from rag import delete_document, ingest_document, list_documents, retrieve_context

load_dotenv()

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".doc", ".md"}

app = FastAPI(title="RAG Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def root():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/admin")
def admin():
    return FileResponse(str(FRONTEND_DIR / "admin.html"))


# ── Documents ──────────────────────────────────────────────────────────────

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    dest = UPLOAD_DIR / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    chunks = ingest_document(dest, file.filename)
    return {"filename": file.filename, "chunks": chunks, "message": f"Đã xử lý {chunks} đoạn văn bản"}


@app.get("/api/documents")
def get_documents():
    return list_documents()


@app.delete("/api/documents/{filename}")
def remove_document(filename: str):
    deleted = delete_document(filename)
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        file_path.unlink()
    return {"deleted_chunks": deleted, "message": f"Đã xóa {deleted} đoạn văn bản"}


# ── Chat ───────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []


@app.post("/api/chat")
def chat(req: ChatRequest):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY chưa được cấu hình")

    # Retrieve relevant context
    context_chunks = retrieve_context(req.message, top_k=5)

    if context_chunks:
        context_text = "\n\n---\n\n".join(context_chunks)
        system_prompt = (
            "Bạn là trợ lý hỏi đáp thông minh. Trả lời câu hỏi dựa trên ngữ cảnh tài liệu bên dưới. "
            "Nếu câu hỏi không liên quan đến tài liệu, hãy trả lời dựa trên kiến thức chung. "
            "Trả lời bằng tiếng Việt nếu câu hỏi bằng tiếng Việt.\n\n"
            f"### Nội dung tài liệu liên quan:\n{context_text}"
        )
    else:
        system_prompt = (
            "Bạn là trợ lý hỏi đáp thông minh. Chưa có tài liệu nào được tải lên. "
            "Hãy trả lời dựa trên kiến thức chung và gợi ý người dùng tải tài liệu lên. "
            "Trả lời bằng tiếng Việt nếu câu hỏi bằng tiếng Việt."
        )

    client = anthropic.Anthropic(api_key=api_key)

    messages = [{"role": m.role, "content": m.content} for m in req.history]
    messages.append({"role": "user", "content": req.message})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system_prompt,
        messages=messages,
    )

    answer = response.content[0].text
    sources = list({c for chunk in context_chunks for c in [chunk]})
    return {
        "answer": answer,
        "has_context": len(context_chunks) > 0,
        "context_count": len(context_chunks),
    }
