from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db import crud
from backend.resumes.resume_processor import save_resume_file, extract_text, index_resume_in_chroma

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.get("")
async def list_resumes(db: AsyncSession = Depends(get_db)):
    return await crud.list_resumes(db)


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    is_base: bool = True,
    db: AsyncSession = Depends(get_db),
):
    contents = await file.read()
    file_path = save_resume_file(contents, file.filename)
    text = extract_text(file_path)
    resume = await crud.create_resume(db, {
        "version": "base" if is_base else "uploaded",
        "file_path": file_path,
        "content_text": text,
        "is_base": is_base,
    })
    index_resume_in_chroma(resume.id, text, {"version": resume.version})
    return {"id": resume.id, "file_path": file_path, "chars": len(text)}


@router.get("/{resume_id}")
async def get_resume(resume_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from backend.db.models import Resume
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Resume not found")
    return r


@router.get("/{resume_id}/text")
async def get_resume_text(resume_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from backend.db.models import Resume
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Resume not found")
    return {"text": r.content_text or extract_text(r.file_path)}
