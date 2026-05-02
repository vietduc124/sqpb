import os
import time
import uuid
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai

load_dotenv(Path(__file__).parent / ".env", override=True)
from pypdf import PdfReader
import docx

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

EMBED_MODEL = "models/gemini-embedding-001"
EMBED_DIM   = 3072
INDEX_NAME  = os.getenv("PINECONE_INDEX_NAME", "rag-chatbot")
CHUNK_SIZE  = 800
CHUNK_OVERLAP = 100


def _chunk_text(text: str) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= CHUNK_SIZE:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
                current = current[-CHUNK_OVERLAP:].strip()
            # paragraph itself too long → split by sentence
            if len(para) > CHUNK_SIZE:
                for sent in para.replace(". ", ".\n").split("\n"):
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(current) + len(sent) + 1 <= CHUNK_SIZE:
                        current = (current + " " + sent).strip()
                    else:
                        if current:
                            chunks.append(current)
                            current = current[-CHUNK_OVERLAP:].strip()
                        # sentence itself too long → hard split
                        for i in range(0, len(sent), CHUNK_SIZE - CHUNK_OVERLAP):
                            chunks.append(sent[i : i + CHUNK_SIZE])
                        current = ""
            else:
                current = para

    if current:
        chunks.append(current)
    return chunks


def _get_index():
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    existing = {i.name: i for i in pc.list_indexes()}

    if INDEX_NAME in existing:
        info = existing[INDEX_NAME]
        # Recreate if wrong dimension or not a dense index
        dim = getattr(info, "dimension", None)
        if dim != EMBED_DIM:
            pc.delete_index(INDEX_NAME)
            existing.pop(INDEX_NAME)

    if INDEX_NAME not in existing:
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    return pc.Index(INDEX_NAME)


EMBED_BATCH = 50  # 50 texts/call, ~0.7s delay → dưới 100 req/phút

def _embed(texts: List[str], input_type: str = "passage") -> List[List[float]]:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    task_type = "retrieval_document" if input_type == "passage" else "retrieval_query"
    vectors = []
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i : i + EMBED_BATCH]
        for attempt in range(5):
            try:
                result = genai.embed_content(
                    model=EMBED_MODEL,
                    content=batch,
                    task_type=task_type,
                )
                embeddings = result["embedding"]
                if isinstance(embeddings[0], float):
                    embeddings = [embeddings]
                vectors.extend(embeddings)
                break
            except Exception as e:
                if "429" in str(e) and attempt < 4:
                    time.sleep(60)  # chờ quota reset
                else:
                    raise
        if i + EMBED_BATCH < len(texts):
            time.sleep(0.7)
    return vectors


def _extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix in (".docx", ".doc"):
        doc = docx.Document(str(file_path))
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        return file_path.read_text(encoding="utf-8", errors="ignore")


def ingest_document(file_path: Path, filename: str) -> int:
    text = _extract_text(file_path)
    if not text.strip():
        return 0

    chunks = _chunk_text(text)
    if not chunks:
        return 0

    index = _get_index()
    vectors = _embed(chunks)

    records = [
        {
            "id": str(uuid.uuid4()),
            "values": vec,
            "metadata": {"text": chunk, "source": filename, "chunk_index": i},
        }
        for i, (chunk, vec) in enumerate(zip(chunks, vectors))
    ]

    for i in range(0, len(records), 100):
        index.upsert(vectors=records[i : i + 100])

    return len(chunks)


def list_documents() -> List[dict]:
    index = _get_index()
    result = index.query(vector=[0.0] * EMBED_DIM, top_k=10000, include_metadata=True)
    counts: dict[str, int] = {}
    for match in result.matches:
        src = match.metadata.get("source", "unknown")
        counts[src] = counts.get(src, 0) + 1
    return [{"name": name, "chunks": count} for name, count in counts.items()]


def delete_document(filename: str) -> int:
    index = _get_index()
    result = index.query(
        vector=[0.0] * EMBED_DIM,
        top_k=10000,
        include_metadata=True,
        filter={"source": {"$eq": filename}},
    )
    ids = [m.id for m in result.matches]
    if ids:
        index.delete(ids=ids)
    return len(ids)


def retrieve_context(query: str, top_k: int = 5) -> List[str]:
    index = _get_index()
    if index.describe_index_stats().total_vector_count == 0:
        return []
    query_vec = _embed([query], input_type="query")[0]
    result = index.query(vector=query_vec, top_k=top_k, include_metadata=True)
    return [m.metadata["text"] for m in result.matches if m.metadata.get("text")]
