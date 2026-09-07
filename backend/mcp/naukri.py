"""Naukri connector stub."""
import asyncio
import uuid
from datetime import datetime
from backend.mcp.base import BaseConnector, RawJob
from backend.config import get_settings

settings = get_settings()


class NaukriConnector(BaseConnector):
    platform = "naukri"

    async def search(self, keywords: str, location: str = "", limit: int = 20) -> list[RawJob]:
        await asyncio.sleep(0)
        return [
            RawJob(
                external_id=f"nk_{uuid.uuid4().hex[:8]}",
                title=f"Senior {keywords} Developer",
                company="Infosys Digital",
                platform=self.platform,
                apply_url="https://www.naukri.com/job-listings-senior-engineer",
                location=location or "Bangalore, India",
                salary_raw="₹18L – ₹28L",
                salary_min=1800000,
                salary_max=2800000,
                salary_currency="INR",
                job_description=(
                    f"Exciting opportunity for a Senior {keywords} Developer at Infosys Digital. "
                    "Work on enterprise-scale projects for Fortune 500 clients."
                ),
                requirements=[
                    f"4+ years in {keywords}",
                    "Agile / Scrum experience",
                    "Strong communication skills",
                ],
                skills_required=[keywords, "Java", "Spring Boot", "Microservices"],
                is_easy_apply=False,
                remote_type="hybrid",
                job_type="full-time",
                posted_at=datetime.utcnow(),
            )
            for _ in range(min(limit, 2))
        ]

    async def get_details(self, job: RawJob) -> RawJob:
        return job
