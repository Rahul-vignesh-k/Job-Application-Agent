"""Resume upload, text extraction, and ChromaDB indexing."""
import os
import uuid
from pathlib import Path
from typing import Optional

from backend.config import get_settings
from backend.rag.chromadb_client import upsert_document, COLLECTION_RESUMES

settings = get_settings()


def extract_text_from_pdf(file_path: str) -> str:
    try:
        from pdfminer.high_level import extract_text
        return extract_text(file_path)
    except Exception:
        pass
    try:
        import PyPDF2
        text = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


def extract_text_from_docx(file_path: str) -> str:
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return f"[DOCX extraction failed: {e}]"


def extract_text(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    if ext in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    if ext == ".txt":
        return Path(file_path).read_text(encoding="utf-8", errors="replace")
    return ""


def save_resume_file(file_bytes: bytes, filename: str) -> str:
    """Save uploaded file to disk and return its path."""
    dest_dir = Path(settings.resume_upload_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex[:8]}_{Path(filename).name}"
    dest_path = dest_dir / safe_name
    dest_path.write_bytes(file_bytes)
    return str(dest_path)


def index_resume_in_chroma(resume_id: str, text: str, metadata: Optional[dict] = None):
    """Chunk the resume text and store in ChromaDB for RAG."""
    chunks = _chunk_text(text, chunk_size=512, overlap=64)
    for i, chunk in enumerate(chunks):
        upsert_document(
            COLLECTION_RESUMES,
            f"{resume_id}_chunk_{i}",
            chunk,
            {**(metadata or {}), "resume_id": resume_id, "chunk_index": i},
        )


def _chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
    return chunks or [text]
