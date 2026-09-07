from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.database import get_db
from backend.db.models import AgentLog, Application
from backend.db import crud

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/applications")
async def applications(limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.list_applications(db, limit=limit)


@router.get("/logs")
async def logs(limit: int = 200, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit)
    )
    rows = list(result.scalars().all())
    return [
        {
            "id": r.id,
            "job_id": r.job_id,
            "event": r.event,
            "level": r.level,
            "message": r.message,
            "agent_name": (r.extra or {}).get("agent"),
            "decision": (r.extra or {}).get("decision"),
            "decision_reason": (r.extra or {}).get("decision_reason"),
            "extra": r.extra,
            "created_at": r.created_at,
        }
        for r in rows
    ]
