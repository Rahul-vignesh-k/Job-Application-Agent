"""ResumeTailorAgent — AI resume tailoring via Gemini + RAG."""
from __future__ import annotations
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from backend.agents.schemas import (
    AgentName, AgentDecision,
    ResumeTailorInput, ResumeTailorOutput,
    AuditInput,
)
from backend.agents.audit_agent import AuditAgent
from backend.config import get_settings
from backend.db import crud
from backend.db.models import JobStatus
from backend.rag.matcher import tailor_resume
from backend.resumes.resume_processor import extract_text

settings = get_settings()
_audit = AuditAgent()


class ResumeTailorAgent:
    name = AgentName.RESUME_TAILOR

    async def run(self, db: AsyncSession, inp: ResumeTailorInput) -> ResumeTailorOutput:
        job = await crud.get_job(db, inp.job_id)
        if not job:
            raise ValueError(f"Job {inp.job_id} not found")

        # Load source resume
        if inp.resume_id:
            from sqlalchemy import select
            from backend.db.models import Resume
            result = await db.execute(select(Resume).where(Resume.id == inp.resume_id))
            resume = result.scalar_one_or_none()
        else:
            resume = await crud.get_base_resume(db)

        if not resume:
            raise ValueError("No base resume found. Upload one first.")

        resume_text = resume.content_text or extract_text(resume.file_path)
        jd_text = job.job_description or ""
        gaps = (job.match_details or {}).get("gaps", [])

        await crud.update_job_status(db, inp.job_id, JobStatus.TAILORING)

        tailored_text = await tailor_resume(resume_text, jd_text, gaps)

        # Persist tailored version
        tailored_path = f"{settings.resume_upload_dir}/tailored_{inp.job_id}.txt"
        Path(tailored_path).write_text(tailored_text, encoding="utf-8")

        diff_summary = (
            f"Tailored for {job.title} @ {job.company}. "
            f"Addressed {len(gaps)} gap(s). "
            f"Classification: {job.job_classification or 'unknown'}."
        )

        new_resume = await crud.create_resume(db, {
            "version": f"tailored_{inp.job_id}",
            "file_path": tailored_path,
            "content_text": tailored_text,
            "is_base": False,
            "tailored_for_job": inp.job_id,
            "diff_summary": diff_summary,
        })

        output = ResumeTailorOutput(
            job_id=inp.job_id,
            tailored_resume_id=new_resume.id,
            tailored_text=tailored_text,
            diff_summary=diff_summary,
            decision=AgentDecision.AWAIT_APPROVAL,
            decision_reason="tailored_resume_ready_for_user_review",
        )

        await _audit.log(db, AuditInput(
            agent_name=self.name, event="resume_tailored",
            job_id=inp.job_id,
            message=f"Tailored resume created: {new_resume.id}",
            decision=output.decision,
            decision_reason=output.decision_reason,
            extra={"resume_id": new_resume.id, "gaps_addressed": len(gaps)},
        ))

        return output
