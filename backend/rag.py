import os
import uuid
from pathlib import Path
from typing import List

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import docx

UPLOAD_PATH = Path(__file__).parent / "uploads"

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM   = 1536
INDEX_NAME  = os.getenv("PINECONE_INDEX_NAME", "rag-chatbot")

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", " ", ""],
)


def _get_index():
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    existing = [i.name for i in pc.list_indexes()]
    if INDEX_NAME not in existing:
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(INDEX_NAME)


def _embed(texts: List[str]) -> List[List[float]]:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in response.data]


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

    chunks = _splitter.split_text(text)
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
    result = index.query(
        vector=[0.0] * EMBED_DIM,
        top_k=10000,
        include_metadata=True,
    )
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
    stats = index.describe_index_stats()
    if stats.total_vector_count == 0:
        return []

    query_vec = _embed([query])[0]
    result = index.query(vector=query_vec, top_k=top_k, include_metadata=True)
    return [m.metadata["text"] for m in result.matches if m.metadata.get("text")]
