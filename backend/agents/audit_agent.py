"""AuditAgent — logs every agent decision and event to the DB."""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from backend.agents.schemas import AuditInput, AgentName
from backend.db import crud


class AuditAgent:
    name = AgentName.AUDIT

    async def log(self, db: AsyncSession, payload: AuditInput) -> None:
        await crud.log_event(
            db,
            event=payload.event,
            message=payload.message,
            job_id=payload.job_id,
            level=payload.level,
            metadata={
                "agent": payload.agent_name,
                "decision": payload.decision,
                "decision_reason": payload.decision_reason,
                **(payload.extra or {}),
            },
        )
