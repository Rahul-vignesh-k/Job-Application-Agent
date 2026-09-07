"""SourcingAgent — discovers jobs via MCP connectors."""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from backend.agents.schemas import (
    AgentName, AgentDecision,
    SourcingInput, SourcingOutput,
    AuditInput,
)
from backend.agents.audit_agent import AuditAgent
from backend.config import get_settings
from backend.db import crud
from backend.db.models import JobStatus
from backend.mcp import CONNECTORS

settings = get_settings()
_audit = AuditAgent()

# Credential fields required per platform (empty string = no credentials needed)
_PLATFORM_CREDS: dict[str, tuple[str, str]] = {
    "linkedin":  ("linkedin_email",  "linkedin_password"),
    "naukri":    ("naukri_email",    "naukri_password"),
    "indeed":    ("indeed_email",    "indeed_password"),
    "glassdoor": ("",                ""),
}


def _platform_enabled(platform: str) -> bool:
    email_field, pass_field = _PLATFORM_CREDS.get(platform, ("", ""))
    if not email_field:
        return True
    return bool(getattr(settings, email_field, "")) and bool(getattr(settings, pass_field, ""))


class SourcingAgent:
    name = AgentName.SOURCING

    async def run(self, db: AsyncSession, inp: SourcingInput) -> SourcingOutput:
        job_ids: list[str] = []
        skipped: list[str] = []
        failed: list[str] = []

        for platform in inp.platforms:
            connector_cls = CONNECTORS.get(platform)
            if not connector_cls:
                continue

            if not _platform_enabled(platform):
                skipped.append(platform)
                await _audit.log(db, AuditInput(
                    agent_name=self.name, event="platform_skipped",
                    level="warning",
                    message=f"{platform.capitalize()} credentials missing — skipping",
                    decision=AgentDecision.SKIP,
                    decision_reason="missing_credentials",
                ))
                continue

            connector = connector_cls()
            try:
                raw_jobs = await connector.search(inp.keywords, inp.location, inp.limit)
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
                    job_ids.append(job.id)

                await _audit.log(db, AuditInput(
                    agent_name=self.name, event="jobs_sourced",
                    message=f"Sourced {len(raw_jobs)} jobs from {platform}",
                    decision=AgentDecision.PROCEED,
                    decision_reason="connector_success",
                    extra={"platform": platform, "count": len(raw_jobs)},
                ))
            except Exception as exc:
                failed.append(platform)
                await _audit.log(db, AuditInput(
                    agent_name=self.name, event="connector_error",
                    level="error",
                    message=f"{platform} connector failed: {exc}",
                    decision=AgentDecision.FAIL,
                    decision_reason=str(exc),
                ))
            finally:
                await connector.close()

        return SourcingOutput(
            jobs_found=len(job_ids),
            job_ids=job_ids,
            skipped_platforms=skipped,
            failed_platforms=failed,
        )
