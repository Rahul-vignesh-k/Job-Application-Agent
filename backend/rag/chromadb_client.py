"""ChromaDB singleton client + collection helpers."""
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.config import get_settings

_client: chromadb.ClientAPI | None = None

COLLECTION_RESUMES = "resumes"
COLLECTION_JOB_ANSWERS = "job_answers"
COLLECTION_JD = "job_descriptions"


def get_chroma_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_collection(name: str):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_document(collection_name: str, doc_id: str, text: str, metadata: dict | None = None):
    col = get_collection(collection_name)
    col.upsert(
        ids=[doc_id],
        documents=[text],
        metadatas=[metadata or {}],
    )


def query_similar(collection_name: str, query_text: str, n_results: int = 5) -> list[dict]:
    col = get_collection(collection_name)
    results = col.query(
        query_texts=[query_text],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    return [
        {"text": d, "metadata": m, "distance": dist}
        for d, m, dist in zip(docs, metas, distances)
    ]


def delete_document(collection_name: str, doc_id: str):
    col = get_collection(collection_name)
    col.delete(ids=[doc_id])
