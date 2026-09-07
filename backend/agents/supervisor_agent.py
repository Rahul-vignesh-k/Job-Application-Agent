"""SupervisorAgent — coordinates the full job-application pipeline."""
from __future__ import annotations
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.schemas import (
    AgentName, AgentDecision, SupervisorState,
    SourcingInput, SourcingOutput,
    JobAnalysisInput, JobAnalysisOutput,
    ResumeTailorInput, ResumeTailorOutput,
    ApplicationInput, ApplicationOutput,
    AuditInput,
)
from backend.agents.sourcing_agent   import SourcingAgent
from backend.agents.job_analysis_agent import JobAnalysisAgent
from backend.agents.resume_tailor_agent import ResumeTailorAgent
from backend.agents.application_agent  import ApplicationAgent
from backend.agents.memory_agent       import MemoryAgent
from backend.agents.audit_agent        import AuditAgent


class SupervisorAgent:
    """
    Routes tasks between specialist agents and manages approval gates.

    Workflow:
      Source → Analyse → (score >= threshold) → Apply
                       → (score < threshold)  → [user gate] → Tailor → [user gate] → Apply
                                                             → Apply with base resume
      Apply  → unknown field → MemoryAgent lookup → (found) → continue
                                                  → (not found) → AWAIT_APPROVAL (manual input)
    """

    name = AgentName.SUPERVISOR

    def __init__(self):
        self.sourcing   = SourcingAgent()
        self.analysis   = JobAnalysisAgent()
        self.tailor     = ResumeTailorAgent()
        self.applicator = ApplicationAgent()
        self.memory     = MemoryAgent()
        self.audit      = AuditAgent()

    # ── Top-level orchestration ───────────────────────────────────────────────

    async def discover_and_queue(
        self,
        db: AsyncSession,
        keywords: str,
        location: str = "",
        platforms: list[str] = None,
        limit: int = 20,
    ) -> SourcingOutput:
        inp = SourcingInput(
            keywords=keywords,
            location=location,
            platforms=platforms or ["linkedin", "naukri", "indeed", "glassdoor"],
            limit=limit,
        )
        result = await self.sourcing.run(db, inp)
        await self.audit.log(db, AuditInput(
            agent_name=self.name, event="discover_complete",
            message=(
                f"Discovered {result.jobs_found} jobs. "
                f"Skipped: {result.skipped_platforms}. Failed: {result.failed_platforms}."
            ),
            decision=AgentDecision.ROUTE,
            decision_reason="routing_to_analysis_queue",
        ))
        return result

    async def analyse_job(
        self,
        db: AsyncSession,
        job_id: str,
    ) -> JobAnalysisOutput:
        result = await self.analysis.run(db, JobAnalysisInput(job_id=job_id))
        await self.audit.log(db, AuditInput(
            agent_name=self.name, event="analysis_routed",
            job_id=job_id,
            message=f"Analysis done. Score={result.match_score}. Routing: {result.decision}.",
            decision=result.decision,
            decision_reason=result.decision_reason,
        ))
        return result

    async def tailor_resume(
        self,
        db: AsyncSession,
        job_id: str,
        resume_id: Optional[str] = None,
    ) -> ResumeTailorOutput:
        result = await self.tailor.run(db, ResumeTailorInput(job_id=job_id, resume_id=resume_id))
        await self.audit.log(db, AuditInput(
            agent_name=self.name, event="tailor_routed",
            job_id=job_id,
            message=f"Tailoring done. Awaiting user approval for {result.tailored_resume_id}.",
            decision=result.decision,
            decision_reason=result.decision_reason,
        ))
        return result

    async def apply_to_job(
        self,
        db: AsyncSession,
        job_id: str,
        resume_id: Optional[str] = None,
    ) -> ApplicationOutput:
        result = await self.applicator.run(db, ApplicationInput(job_id=job_id, resume_id=resume_id))
        await self.audit.log(db, AuditInput(
            agent_name=self.name, event="apply_routed",
            job_id=job_id,
            message=f"Application attempt complete. Decision: {result.decision}.",
            decision=result.decision,
            decision_reason=result.decision_reason,
        ))
        return result

    async def resolve_fields_and_retry(
        self,
        db: AsyncSession,
        job_id: str,
        answers: dict,
    ) -> None:
        """
        Save resolved field answers via MemoryAgent, then status returns to APPLYING
        so the next apply call can proceed.
        """
        from backend.db import crud
        from backend.agents.schemas import MemorySaveInput

        for field_id, answer in answers.items():
            from sqlalchemy import select
            from backend.db.models import PendingFormField
            result = await db.execute(
                select(PendingFormField).where(PendingFormField.id == field_id)
            )
            pf = result.scalar_one_or_none()
            if pf:
                await crud.resolve_pending_field(db, field_id, answer)
                await self.memory.save(db, MemorySaveInput(
                    field_key=pf.field_key,
                    field_label=pf.field_label or pf.field_key,
                    answer=answer,
                ))

        await self.audit.log(db, AuditInput(
            agent_name=self.name, event="fields_resolved",
            job_id=job_id,
            message=f"Resolved {len(answers)} pending field(s) via MemoryAgent.",
            decision=AgentDecision.PROCEED,
            decision_reason="fields_resolved_ready_to_retry",
        ))
