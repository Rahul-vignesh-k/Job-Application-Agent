"""Glassdoor connector stub."""
import asyncio
import uuid
from datetime import datetime
from backend.mcp.base import BaseConnector, RawJob
from backend.config import get_settings

settings = get_settings()


class GlassdoorConnector(BaseConnector):
    platform = "glassdoor"

    async def search(self, keywords: str, location: str = "", limit: int = 20) -> list[RawJob]:
        await asyncio.sleep(0)
        return [
            RawJob(
                external_id=f"gd_{uuid.uuid4().hex[:8]}",
                title=f"Lead {keywords} Engineer",
                company="Enterprise Solutions Corp",
                platform=self.platform,
                apply_url="https://www.glassdoor.com/job-listing/lead-engineer",
                location=location or "New York, NY",
                salary_raw="$140k – $180k",
                salary_min=140000,
                salary_max=180000,
                job_description=(
                    f"We're hiring a Lead {keywords} Engineer to drive technical strategy "
                    "and mentor a team of 5+ engineers."
                ),
                requirements=[
                    f"7+ years of {keywords} engineering",
                    "Leadership experience",
                    "System design expertise",
                    "MS/BS in CS or equivalent",
                ],
                skills_required=[keywords, "Kubernetes", "Terraform", "Go", "Python"],
                is_easy_apply=False,
                remote_type="hybrid",
                job_type="full-time",
                posted_at=datetime.utcnow(),
            )
            for _ in range(min(limit, 2))
        ]

    async def get_details(self, job: RawJob) -> RawJob:
        return job
