"""JobAnalysisAgent — JD extraction, classification, match scoring via Gemini + RAG."""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from backend.agents.schemas import (
    AgentName, AgentDecision,
    JobAnalysisInput, JobAnalysisOutput, GapItem,
    AuditInput,
)
from backend.agents.audit_agent import AuditAgent
from backend.config import get_settings
from backend.db import crud
from backend.db.models import JobStatus
from backend.rag.matcher import match_resume_to_jd, classify_job_type
from backend.resumes.resume_processor import extract_text

settings = get_settings()
_audit = AuditAgent()


class JobAnalysisAgent:
    name = AgentName.JOB_ANALYSIS

    async def run(self, db: AsyncSession, inp: JobAnalysisInput) -> JobAnalysisOutput:
        job = await crud.get_job(db, inp.job_id)
        if not job:
            raise ValueError(f"Job {inp.job_id} not found")

        await crud.update_job_status(db, inp.job_id, JobStatus.ANALYZING)

        # Load resume text
        resume = await crud.get_base_resume(db)
        resume_text = ""
        if resume:
            resume_text = resume.content_text or extract_text(resume.file_path)

        jd_text = job.job_description or ""

        # Classify Internship vs FTE
        classification = await classify_job_type(job.title, jd_text)
        await crud.set_job_classification(db, inp.job_id, classification)

        # Gemini + RAG match analysis
        raw = await match_resume_to_jd(resume_text, jd_text, inp.job_id)

        score = int(raw.get("match_score", 0))
        gaps = [GapItem(**g) for g in raw.get("gaps", [])]
        recommendation = raw.get("recommendation", "review_required")

        # Decision
        if score >= settings.auto_apply_threshold:
            decision = AgentDecision.PROCEED
            decision_reason = f"score {score} >= threshold {settings.auto_apply_threshold}"
            new_status = JobStatus.READY_TO_APPLY
        else:
            decision = AgentDecision.AWAIT_APPROVAL
            decision_reason = f"score {score} < threshold {settings.auto_apply_threshold}, needs review"
            new_status = JobStatus.REVIEW_REQUIRED

        await crud.set_job_score(db, inp.job_id, float(score), raw)
        await crud.update_job_status(db, inp.job_id, new_status)

        output = JobAnalysisOutput(
            job_id=inp.job_id,
            job_classification=classification,
            match_score=score,
            matched_skills=raw.get("matched_skills", []),
            missing_skills=raw.get("missing_skills", []),
            gaps=gaps,
            overall_summary=raw.get("overall_summary", ""),
            recommendation=recommendation,
            decision=decision,
            decision_reason=decision_reason,
        )

        await _audit.log(db, AuditInput(
            agent_name=self.name, event="analysis_complete",
            job_id=inp.job_id,
            message=f"Score: {score} | Type: {classification} | Decision: {decision}",
            decision=decision,
            decision_reason=decision_reason,
            extra={"score": score, "classification": classification, "recommendation": recommendation},
        ))

        return output
