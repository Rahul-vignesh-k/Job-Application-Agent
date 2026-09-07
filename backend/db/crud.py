"""CRUD helpers — thin layer over SQLAlchemy async sessions."""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import (
    Job, Resume, Application, SavedAnswer, PendingFormField, AgentLog,
    JobStatus, ApplicationResult,
)


def _uid() -> str:
    return str(uuid.uuid4())


# ── Jobs ──────────────────────────────────────────────────────────────────────

async def create_job(db: AsyncSession, data: dict) -> Job:
    job = Job(id=data.get("id", _uid()), **{k: v for k, v in data.items() if k != "id"})
    db.add(job)
    await db.flush()
    return job


async def get_job(db: AsyncSession, job_id: str) -> Optional[Job]:
    result = await db.execute(select(Job).where(Job.id == job_id))
    return result.scalar_one_or_none()


async def list_jobs(
    db: AsyncSession,
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Job]:
    q = select(Job).order_by(Job.discovered_at.desc())
    if status:
        q = q.where(Job.status == status)
    if platform:
        q = q.where(Job.platform == platform)
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_job_status(db: AsyncSession, job_id: str, status: JobStatus) -> None:
    await db.execute(
        update(Job).where(Job.id == job_id).values(status=status, updated_at=datetime.now(timezone.utc))
    )


async def set_job_score(db: AsyncSession, job_id: str, score: float, details: dict) -> None:
    await db.execute(
        update(Job).where(Job.id == job_id).values(
            match_score=score, match_details=details, updated_at=datetime.now(timezone.utc)
        )
    )


async def set_job_classification(db: AsyncSession, job_id: str, classification: str) -> None:
    await db.execute(
        update(Job).where(Job.id == job_id).values(
            job_classification=classification, updated_at=datetime.now(timezone.utc)
        )
    )


async def count_jobs_by_status(db: AsyncSession) -> dict:
    rows = await db.execute(
        select(Job.status, func.count(Job.id)).group_by(Job.status)
    )
    return {row[0]: row[1] for row in rows.all()}


# ── Resumes ───────────────────────────────────────────────────────────────────

async def create_resume(db: AsyncSession, data: dict) -> Resume:
    resume = Resume(id=_uid(), **data)
    db.add(resume)
    await db.flush()
    return resume


async def get_base_resume(db: AsyncSession) -> Optional[Resume]:
    result = await db.execute(select(Resume).where(Resume.is_base == True).order_by(Resume.created_at.desc()))
    return result.scalar_one_or_none()


async def list_resumes(db: AsyncSession) -> List[Resume]:
    result = await db.execute(select(Resume).order_by(Resume.created_at.desc()))
    return list(result.scalars().all())


# ── Applications ──────────────────────────────────────────────────────────────

async def create_application(db: AsyncSession, job_id: str, resume_id: Optional[str]) -> Application:
    app = Application(id=_uid(), job_id=job_id, resume_id=resume_id)
    db.add(app)
    await db.flush()
    return app


async def update_application(db: AsyncSession, app_id: str, **kwargs) -> None:
    await db.execute(
        update(Application).where(Application.id == app_id).values(**kwargs, updated_at=datetime.now(timezone.utc))
    )


async def list_applications(db: AsyncSession, limit: int = 100) -> List[Application]:
    result = await db.execute(
        select(Application).order_by(Application.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


# ── Saved Answers ─────────────────────────────────────────────────────────────

async def upsert_saved_answer(db: AsyncSession, field_key: str, answer: str, **kwargs) -> SavedAnswer:
    result = await db.execute(select(SavedAnswer).where(SavedAnswer.field_key == field_key))
    existing = result.scalar_one_or_none()
    if existing:
        existing.answer = answer
        existing.updated_at = datetime.now(timezone.utc)
        for k, v in kwargs.items():
            setattr(existing, k, v)
        return existing
    sa = SavedAnswer(id=_uid(), field_key=field_key, answer=answer, **kwargs)
    db.add(sa)
    await db.flush()
    return sa


async def get_saved_answer(db: AsyncSession, field_key: str) -> Optional[SavedAnswer]:
    result = await db.execute(select(SavedAnswer).where(SavedAnswer.field_key == field_key))
    return result.scalar_one_or_none()


async def list_saved_answers(db: AsyncSession) -> List[SavedAnswer]:
    result = await db.execute(select(SavedAnswer).order_by(SavedAnswer.field_key))
    return list(result.scalars().all())


# ── Pending Fields ────────────────────────────────────────────────────────────

async def create_pending_field(db: AsyncSession, job_id: str, data: dict) -> PendingFormField:
    pf = PendingFormField(id=_uid(), job_id=job_id, **data)
    db.add(pf)
    await db.flush()
    return pf


async def resolve_pending_field(db: AsyncSession, field_id: str, answer: str) -> None:
    await db.execute(
        update(PendingFormField).where(PendingFormField.id == field_id).values(is_resolved=True, answer=answer)
    )


async def list_pending_fields(db: AsyncSession, job_id: str) -> List[PendingFormField]:
    result = await db.execute(
        select(PendingFormField).where(PendingFormField.job_id == job_id, PendingFormField.is_resolved == False)
    )
    return list(result.scalars().all())


# ── Logs ──────────────────────────────────────────────────────────────────────

async def log_event(db: AsyncSession, event: str, message: str, job_id: Optional[str] = None,
                    level: str = "info", metadata: Optional[dict] = None) -> None:
    entry = AgentLog(id=_uid(), job_id=job_id, event=event, message=message, level=level, extra=metadata)
    db.add(entry)
    await db.flush()
