"""Indeed connector stub."""
import asyncio
import uuid
from datetime import datetime
from backend.mcp.base import BaseConnector, RawJob
from backend.config import get_settings

settings = get_settings()


class IndeedConnector(BaseConnector):
    platform = "indeed"

    async def search(self, keywords: str, location: str = "", limit: int = 20) -> list[RawJob]:
        await asyncio.sleep(0)
        return [
            RawJob(
                external_id=f"in_{uuid.uuid4().hex[:8]}",
                title=f"{keywords} Specialist",
                company="Startup Innovations LLC",
                platform=self.platform,
                apply_url="https://www.indeed.com/viewjob?jk=abc123",
                location=location or "Austin, TX",
                salary_raw="$90k – $130k / year",
                salary_min=90000,
                salary_max=130000,
                job_description=(
                    f"Join our fast-growing team as a {keywords} Specialist. "
                    "We value curiosity, impact, and a growth mindset."
                ),
                requirements=[
                    f"3+ years of {keywords}",
                    "Startup experience preferred",
                ],
                skills_required=[keywords, "React", "Node.js", "PostgreSQL"],
                is_easy_apply=True,
                remote_type="remote",
                job_type="full-time",
                posted_at=datetime.utcnow(),
            )
            for _ in range(min(limit, 2))
        ]

    async def get_details(self, job: RawJob) -> RawJob:
        return job
