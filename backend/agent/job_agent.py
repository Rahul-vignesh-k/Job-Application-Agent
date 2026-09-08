"""Core job-application agent orchestrating the full pipeline."""
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.db import crud
from backend.db.models import JobStatus, ApplicationResult
from backend.agent.state_machine import Event, transition
from backend.mcp import CONNECTORS
from backend.mcp.base import RawJob
from backend.rag.matcher import match_resume_to_jd, tailor_resume, classify_job_type
from backend.automation.applicator import get_applicator, not_submitted_result, UnknownFieldError
from backend.resumes.resume_processor import extract_text
from backend.rag.chromadb_client import upsert_document, COLLECTION_JOB_ANSWERS

settings = get_settings()


_SALARY_FIELDS = frozenset([
    "expected_salary", "expected_ctc", "expected_compensation",
    "desired_salary", "salary_expectation", "ctc_expectation",
    "stipend", "monthly_stipend", "expected_stipend",
])
_PORTFOLIO_FIELDS = frozenset([
    "portfolio_url", "portfolio", "website", "personal_website",
    "project_url", "coding_profile", "coding_url", "online_profile",
])


def _build_form_data(job_classification: str = "FTE", extra: dict = None) -> dict:
    """
    Build the default form data.
    job_classification: 'Internship' | 'FTE' — selects the right expected salary.
    """
    # Pick salary by classification
    expected_salary = (
        settings.user_expected_salary_intern
        if job_classification == "Internship"
        else settings.user_expected_salary_fte
    )

    # Portfolio fallback chain: portfolio_url → leetcode → github → linkedin
    portfolio = (
        settings.user_portfolio_url
        or settings.user_leetcode_url
        or settings.user_github_url
        or settings.user_linkedin_url
        or ""
    )

    data = {
        "full_name": settings.user_full_name,
        "first_name": settings.user_full_name.split()[0] if settings.user_full_name else "",
        "last_name": settings.user_full_name.split()[-1] if settings.user_full_name else "",
        "email": settings.user_email,
        "phone": settings.user_phone,
        "location": settings.user_location,
        "years_experience": str(settings.user_years_experience),
        "current_salary": settings.user_current_salary,
        "expected_salary": expected_salary,
        "expected_ctc": expected_salary,
        "expected_stipend": expected_salary,
        "stipend": expected_salary,
        "notice_period": settings.user_notice_period,
        "linkedin_url": settings.user_linkedin_url,
        "github_url": settings.user_github_url,
        "portfolio_url": portfolio,
        "website": portfolio,
        "coding_profile": settings.user_leetcode_url or settings.user_github_url or "",
        "leetcode_url": settings.user_leetcode_url,
    }
    if extra:
        data.update(extra)
    return data


async def _lookup_answer(db: AsyncSession, field_key: str, field_label: str) -> Optional[str]:
    """
    Priority: .env → SQLite → ChromaDB
    Returns answer string or None.
    """
    # 1. Check env (already in form_data); use FTE as safe default for lookup
    env_data = _build_form_data(job_classification="FTE")
    if field_key in env_data and env_data[field_key]:
        return env_data[field_key]

    # 2. SQLite saved answers
    sa = await crud.get_saved_answer(db, field_key)
    if sa and sa.answer:
        return sa.answer

    # 3. ChromaDB semantic search
    from backend.rag.matcher import lookup_field_answer
    result = await lookup_field_answer(field_key, field_label)
    if result:
        return result["answer"]

    return None


class JobAgent:
    """
    Orchestrates: scrape → analyse → match → tailor → apply.
    Long-running operations run as background asyncio tasks.
    """

    # Credentials required per platform; empty string means "no credentials needed"
    _PLATFORM_CREDS: dict[str, tuple[str, str]] = {
        "linkedin":  ("linkedin_email",  "linkedin_password"),
        "naukri":    ("naukri_email",    "naukri_password"),
        "indeed":    ("indeed_email",    "indeed_password"),
        "glassdoor": ("",                ""),               # no login required for stub
    }

    def _platform_enabled(self, platform: str) -> bool:
        """Return True if the platform has credentials or requires none."""
        email_field, pass_field = self._PLATFORM_CREDS.get(platform, ("", ""))
        if not email_field:
            return True  # no credentials needed
        return bool(getattr(settings, email_field, "")) and bool(getattr(settings, pass_field, ""))

    async def discover_jobs(
        self,
        db: AsyncSession,
        keywords: str,
        location: str = "",
        platforms: list[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """Scrape jobs from enabled platforms; skip any with missing credentials."""
        requested = platforms or list(CONNECTORS.keys())
        all_jobs = []

        for platform in requested:
            connector_cls = CONNECTORS.get(platform)
            if not connector_cls:
                continue

            if not self._platform_enabled(platform):
                await crud.log_event(
                    db, "platform_skipped",
                    f"{platform.capitalize()} credentials missing, skipping platform",
                    level="warning",
                )
                continue

            connector = connector_cls()
            try:
                raw_jobs: list[RawJob] = await connector.search(keywords, location, limit)
                for rj in raw_jobs:
                    job_data = {
                        "id": f"{platform}_{rj.external_id}",
                        "title": rj.title,
                        "company": rj.company,
                        "platform": rj.platform,
                        "location": rj.location,
                        "salary_raw": rj.salary_raw,
                        "salary_min": rj.salary_min,
                        "salary_max": rj.salary_max,
                        "salary_currency": rj.salary_currency,
                        "job_description": rj.job_description,
                        "requirements": rj.requirements,
                        "skills_required": rj.skills_required,
                        "apply_url": rj.apply_url,
                        "external_id": rj.external_id,
                        "is_easy_apply": rj.is_easy_apply,
                        "remote_type": rj.remote_type,
                        "job_type": rj.job_type,
                        "posted_at": rj.posted_at,
                        "status": JobStatus.DISCOVERED,
                    }
                    job = await crud.create_job(db, job_data)
                    await crud.log_event(db, "job_discovered", f"Discovered: {rj.title} @ {rj.company}", job_id=job.id)
                    all_jobs.append(job)
            except Exception as exc:
                await crud.log_event(
                    db, "connector_error",
                    f"{platform} connector failed: {exc}",
                    level="error",
                )
            finally:
                await connector.close()

        return all_jobs

    async def analyse_job(self, db: AsyncSession, job_id: str) -> dict:
        """Run Gemini match analysis for a single job."""
        job = await crud.get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        await crud.update_job_status(db, job_id, JobStatus.ANALYZING)

        resume = await crud.get_base_resume(db)
        resume_text = resume.content_text if resume else ""
        if not resume_text and resume:
            resume_text = extract_text(resume.file_path)

        jd_text = job.job_description or ""

        # Classify Internship vs FTE (fast keyword pass, Gemini fallback)
        classification = await classify_job_type(job.title, jd_text)
        await crud.set_job_classification(db, job_id, classification)

        analysis = await match_resume_to_jd(resume_text, jd_text, job_id)

        score = float(analysis.get("match_score", 0))
        new_status = (
            JobStatus.READY_TO_APPLY
            if score >= settings.auto_apply_threshold
            else JobStatus.REVIEW_REQUIRED
        )
        await crud.set_job_score(db, job_id, score, analysis)
        await crud.update_job_status(db, job_id, new_status)
        await crud.log_event(
            db, "analysis_complete",
            f"Score: {score} | Type: {classification} → {new_status}",
            job_id=job_id,
            metadata={"score": score, "job_classification": classification},
        )
        return {**analysis, "job_classification": classification}

    async def tailor_job_resume(self, db: AsyncSession, job_id: str) -> dict:
        """Create a tailored resume for the given job."""
        job = await crud.get_job(db, job_id)
        resume = await crud.get_base_resume(db)
        if not resume:
            raise ValueError("No base resume found. Upload one first.")

        resume_text = resume.content_text or extract_text(resume.file_path)
        gaps = (job.match_details or {}).get("gaps", [])
        tailored_text = await tailor_resume(resume_text, job.job_description or "", gaps)

        # Save tailored version to DB
        from pathlib import Path
        import os
        tailored_path = f"{settings.resume_upload_dir}/tailored_{job_id}.txt"
        Path(tailored_path).write_text(tailored_text, encoding="utf-8")

        new_resume = await crud.create_resume(db, {
            "version": f"tailored_{job_id}",
            "file_path": tailored_path,
            "content_text": tailored_text,
            "is_base": False,
            "tailored_for_job": job_id,
        })
        await crud.update_job_status(db, job_id, JobStatus.TAILORING)
        return {"resume_id": new_resume.id, "tailored_text": tailored_text}

    async def submit_application(self, db: AsyncSession, job_id: str, resume_id: Optional[str] = None) -> dict:
        """Submit the application via Playwright."""
        job = await crud.get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        applicator = get_applicator()
        if not getattr(applicator, "supports_submission", False):
            result = not_submitted_result()
            await crud.log_event(
                db, "application_not_submitted", result["error"],
                job_id=job_id, level="warning",
                metadata={"submission_status": "not_submitted", "simulated": True},
            )
            return result

        # Check for unresolved pending fields first
        pending = await crud.list_pending_fields(db, job_id)
        if pending:
            return {"status": "waiting_input", "pending_fields": [p.id for p in pending]}

        if not resume_id:
            resume = await crud.get_base_resume(db)
            resume_id = resume.id if resume else None

        resume = None
        if resume_id:
            from sqlalchemy import select
            from backend.db.models import Resume
            async with db.bind.begin() as _:
                pass
            from sqlalchemy import select
            result = await db.execute(
                __import__("sqlalchemy", fromlist=["select"]).select(
                    __import__("backend.db.models", fromlist=["Resume"]).Resume
                ).where(
                    __import__("backend.db.models", fromlist=["Resume"]).Resume.id == resume_id
                )
            )
            resume = result.scalar_one_or_none()

        resume_path = resume.file_path if resume else settings.default_resume_path
        form_data = _build_form_data(job_classification=job.job_classification or "FTE")
        # Merge saved answers
        saved = await crud.list_saved_answers(db)
        for sa in saved:
            form_data[sa.field_key] = sa.answer

        app = await crud.create_application(db, job_id, resume_id)
        await crud.update_job_status(db, job_id, JobStatus.APPLYING)

        try:
            result = await applicator.apply(job.apply_url, resume_path, form_data, job_id)

            if result["success"]:
                await crud.update_application(
                    db, app.id,
                    status=JobStatus.APPLIED,
                    result=ApplicationResult.SUCCESS,
                    applied_at=datetime.now(timezone.utc),
                    screenshot_path=result["screenshot"],
                    confirmation_number=result["confirmation"],
                )
                await crud.update_job_status(db, job_id, JobStatus.APPLIED)
            else:
                await crud.update_application(
                    db, app.id,
                    status=JobStatus.FAILED,
                    result=ApplicationResult.FAILED,
                    error_message=result["error"],
                    screenshot_path=result["screenshot"],
                )
                await crud.update_job_status(db, job_id, JobStatus.FAILED)

            return result
        except UnknownFieldError as e:
            # Pause and record the unknown field
            await crud.create_pending_field(db, job_id, {
                "field_key": e.field_key,
                "field_label": e.field_label,
                "field_type": e.field_type,
                "options": e.options,
            })
            await crud.update_job_status(db, job_id, JobStatus.WAITING_INPUT)
            raise

    async def resolve_pending_fields(self, db: AsyncSession, job_id: str, answers: dict) -> None:
        """Save user-provided answers and resume the application."""
        for field_id, answer in answers.items():
            pf_result = await db.execute(
                __import__("sqlalchemy", fromlist=["select"]).select(
                    __import__("backend.db.models", fromlist=["PendingFormField"]).PendingFormField
                ).where(
                    __import__("backend.db.models", fromlist=["PendingFormField"]).PendingFormField.id == field_id
                )
            )
            pf = pf_result.scalar_one_or_none()
            if pf:
                await crud.resolve_pending_field(db, field_id, answer)
                # Persist answer for future RAG reuse
                await crud.upsert_saved_answer(db, pf.field_key, answer, field_label=pf.field_label, source="manual")
                upsert_document(
                    COLLECTION_JOB_ANSWERS,
                    f"answer_{pf.field_key}",
                    answer,
                    {"field_key": pf.field_key, "field_label": pf.field_label or ""},
                )
