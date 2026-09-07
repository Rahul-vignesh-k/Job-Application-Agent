from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db import crud
from backend.rag.chromadb_client import upsert_document, COLLECTION_JOB_ANSWERS

router = APIRouter(prefix="/answers", tags=["answers"])


class AnswerCreate(BaseModel):
    field_key: str
    field_label: Optional[str] = None
    answer: str
    is_sensitive: bool = False


@router.get("")
async def list_answers(db: AsyncSession = Depends(get_db)):
    return await crud.list_saved_answers(db)


@router.post("")
async def save_answer(payload: AnswerCreate, db: AsyncSession = Depends(get_db)):
    sa = await crud.upsert_saved_answer(
        db,
        payload.field_key,
        payload.answer,
        field_label=payload.field_label,
        is_sensitive=payload.is_sensitive,
        source="manual",
    )
    # Also index in ChromaDB for semantic lookup
    upsert_document(
        COLLECTION_JOB_ANSWERS,
        f"answer_{payload.field_key}",
        payload.answer,
        {"field_key": payload.field_key, "field_label": payload.field_label or ""},
    )
    return sa


@router.delete("/{field_key}")
async def delete_answer(field_key: str, db: AsyncSession = Depends(get_db)):
    sa = await crud.get_saved_answer(db, field_key)
    if not sa:
        raise HTTPException(404, "Answer not found")
    await db.delete(sa)
    return {"deleted": field_key}
