from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db import crud
from backend.db.models import JobStatus
from backend.agents.supervisor_agent import SupervisorAgent

router = APIRouter(prefix="/jobs", tags=["jobs"])
supervisor = SupervisorAgent()


class DiscoverRequest(BaseModel):
    keywords: str
    location: str = ""
    platforms: List[str] = ["linkedin", "naukri", "indeed", "glassdoor"]
    limit: int = 20


class ResolveFieldsRequest(BaseModel):
    answers: dict


@router.get("")
async def list_jobs(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    return await crud.list_jobs(db, status=status, platform=platform, limit=limit, offset=offset)


@router.post("/discover")
async def discover_jobs(req: DiscoverRequest, db: AsyncSession = Depends(get_db)):
    result = await supervisor.discover_and_queue(db, req.keywords, req.location, req.platforms, req.limit)
    return {"discovered": result.jobs_found, "job_ids": result.job_ids,
            "skipped_platforms": result.skipped_platforms, "failed_platforms": result.failed_platforms}


@router.get("/stats")
async def job_stats(db: AsyncSession = Depends(get_db)):
    return await crud.count_jobs_by_status(db)


@router.get("/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await crud.get_job(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.post("/{job_id}/analyse")
async def analyse_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await crud.get_job(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    result = await supervisor.analyse_job(db, job_id)
    return result.model_dump()


@router.post("/{job_id}/tailor")
async def tailor_resume(job_id: str, resume_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    job = await crud.get_job(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    result = await supervisor.tailor_resume(db, job_id, resume_id)
    return result.model_dump()


@router.post("/{job_id}/apply")
async def apply_to_job(job_id: str, resume_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    job = await crud.get_job(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    result = await supervisor.apply_to_job(db, job_id, resume_id)
    return result.model_dump()


@router.post("/{job_id}/resolve-fields")
async def resolve_fields(job_id: str, req: ResolveFieldsRequest, db: AsyncSession = Depends(get_db)):
    await supervisor.resolve_fields_and_retry(db, job_id, req.answers)
    return {"status": "resolved"}


@router.patch("/{job_id}/status")
async def update_status(job_id: str, status: str, db: AsyncSession = Depends(get_db)):
    try:
        s = JobStatus(status)
    except ValueError:
        raise HTTPException(400, f"Invalid status: {status}")
    await crud.update_job_status(db, job_id, s)
    return {"status": status}


@router.get("/{job_id}/pending-fields")
async def pending_fields(job_id: str, db: AsyncSession = Depends(get_db)):
    return await crud.list_pending_fields(db, job_id)
