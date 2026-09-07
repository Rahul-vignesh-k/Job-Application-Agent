"""ApplicationAgent — Playwright form automation with smart form-fill."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.agents.schemas import (
    AgentName, AgentDecision,
    ApplicationInput, ApplicationOutput,
    AuditInput,
)
from backend.agents.audit_agent import AuditAgent
from backend.config import get_settings
from backend.db import crud
from backend.db.models import JobStatus, ApplicationResult
from backend.automation.applicator import get_applicator, UnknownFieldError

settings = get_settings()
_audit = AuditAgent()


def _build_form_data(job_classification: str = "FTE") -> dict:
    """
    Build form data dict with correct salary and portfolio fallback chain.
    job_classification: 'Internship' | 'FTE'
    """
    expected_salary = (
        settings.user_expected_salary_intern
        if job_classification == "Internship"
        else settings.user_expected_salary_fte
    )
    portfolio = (
        settings.user_portfolio_url
        or settings.user_leetcode_url
        or settings.user_github_url
        or settings.user_linkedin_url
        or ""
    )
    return {
        "full_name":        settings.user_full_name,
        "first_name":       settings.user_full_name.split()[0] if settings.user_full_name else "",
        "last_name":        settings.user_full_name.split()[-1] if settings.user_full_name else "",
        "email":            settings.user_email,
        "phone":            settings.user_phone,
        "location":         settings.user_location,
        "years_experience": str(settings.user_years_experience),
        "current_salary":   settings.user_current_salary,
        "expected_salary":  expected_salary,
        "expected_ctc":     expected_salary,
        "expected_stipend": expected_salary,
        "stipend":          expected_salary,
        "notice_period":    settings.user_notice_period,
        "linkedin_url":     settings.user_linkedin_url,
        "github_url":       settings.user_github_url,
        "portfolio_url":    portfolio,
        "website":          portfolio,
        "coding_profile":   settings.user_leetcode_url or settings.user_github_url or "",
        "leetcode_url":     settings.user_leetcode_url,
    }


class ApplicationAgent:
    name = AgentName.APPLICATION

    async def run(self, db: AsyncSession, inp: ApplicationInput) -> ApplicationOutput:
        job = await crud.get_job(db, inp.job_id)
        if not job:
            raise ValueError(f"Job {inp.job_id} not found")

        # Block if pending fields remain
        pending = await crud.list_pending_fields(db, inp.job_id)
        if pending:
            return ApplicationOutput(
                job_id=inp.job_id,
                success=False,
                unknown_fields=[{"id": p.id, "label": p.field_label, "key": p.field_key} for p in pending],
                decision=AgentDecision.AWAIT_APPROVAL,
                decision_reason=f"{len(pending)} unresolved form fields",
            )

        # Resolve resume
        resume_id = inp.resume_id
        if not resume_id:
            base = await crud.get_base_resume(db)
            resume_id = base.id if base else None

        resume_path = settings.default_resume_path
        if resume_id:
            from sqlalchemy import select
            from backend.db.models import Resume
            result = await db.execute(select(Resume).where(Resume.id == resume_id))
            r = result.scalar_one_or_none()
            if r:
                resume_path = r.file_path

        classification = job.job_classification or "FTE"
        form_data = _build_form_data(classification)

        # Merge persisted manual answers
        saved = await crud.list_saved_answers(db)
        for sa in saved:
            form_data[sa.field_key] = sa.answer

        app = await crud.create_application(db, inp.job_id, resume_id)
        await crud.update_job_status(db, inp.job_id, JobStatus.APPLYING)

        try:
            applicator = get_applicator()
            result = await applicator.apply(job.apply_url, resume_path, form_data, inp.job_id)

            if result["success"]:
                await crud.update_application(
                    db, app.id,
                    status=JobStatus.APPLIED,
                    result=ApplicationResult.SUCCESS,
                    applied_at=datetime.now(timezone.utc),
                    screenshot_path=result["screenshot"],
                    confirmation_number=result["confirmation"],
                )
                await crud.update_job_status(db, inp.job_id, JobStatus.APPLIED)

                output = ApplicationOutput(
                    job_id=inp.job_id,
                    success=True,
                    confirmation_number=result["confirmation"],
                    screenshot_path=result["screenshot"],
                    decision=AgentDecision.PROCEED,
                    decision_reason="application_submitted_successfully",
                )
            else:
                await crud.update_application(
                    db, app.id,
                    status=JobStatus.FAILED,
                    result=ApplicationResult.FAILED,
                    error_message=result["error"],
                    screenshot_path=result["screenshot"],
                )
                await crud.update_job_status(db, inp.job_id, JobStatus.FAILED)

                output = ApplicationOutput(
                    job_id=inp.job_id,
                    success=False,
                    error=result["error"],
                    screenshot_path=result["screenshot"],
                    decision=AgentDecision.FAIL,
                    decision_reason=result["error"] or "playwright_error",
                )

        except UnknownFieldError as e:
            await crud.create_pending_field(db, inp.job_id, {
                "field_key":   e.field_key,
                "field_label": e.field_label,
                "field_type":  e.field_type,
                "options":     e.options,
            })
            await crud.update_job_status(db, inp.job_id, JobStatus.WAITING_INPUT)

            output = ApplicationOutput(
                job_id=inp.job_id,
                success=False,
                unknown_fields=[{"key": e.field_key, "label": e.field_label}],
                decision=AgentDecision.AWAIT_APPROVAL,
                decision_reason=f"unknown_field: {e.field_label}",
            )

        await _audit.log(db, AuditInput(
            agent_name=self.name, event="application_attempt",
            job_id=inp.job_id,
            level="info" if output.success else "warning",
            message=(
                f"Applied successfully (conf: {output.confirmation_number})"
                if output.success else f"Application failed: {output.decision_reason}"
            ),
            decision=output.decision,
            decision_reason=output.decision_reason,
            extra={"classification": classification, "salary_used": form_data.get("expected_salary")},
        ))

        return output
