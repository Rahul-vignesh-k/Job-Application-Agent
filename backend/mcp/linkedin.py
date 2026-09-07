"""LinkedIn connector — uses Playwright to scrape Easy Apply jobs."""
import asyncio
import uuid
from datetime import datetime
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page

from backend.mcp.base import BaseConnector, RawJob
from backend.config import get_settings

settings = get_settings()


class LinkedInConnector(BaseConnector):
    platform = "linkedin"

    def __init__(self):
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None

    async def _ensure_browser(self):
        if self._browser is None:
            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(headless=True)
            context = await self._browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            self._page = await context.new_page()

    async def _login(self):
        """Log in to LinkedIn if credentials provided."""
        if not settings.linkedin_email or not settings.linkedin_password:
            return
        await self._page.goto("https://www.linkedin.com/login")
        await self._page.fill("#username", settings.linkedin_email)
        await self._page.fill("#password", settings.linkedin_password)
        await self._page.click('[type="submit"]')
        await self._page.wait_for_load_state("networkidle", timeout=15000)

    async def search(self, keywords: str, location: str = "", limit: int = 20) -> list[RawJob]:
        """
        STUB — returns synthetic data so the rest of the pipeline can be tested
        without valid credentials. Replace with real scraping logic.
        """
        await asyncio.sleep(0)  # yield to event loop

        stub_jobs = [
            RawJob(
                external_id=f"li_{uuid.uuid4().hex[:8]}",
                title=f"{keywords} Engineer",
                company="TechCorp Inc.",
                platform=self.platform,
                apply_url="https://www.linkedin.com/jobs/view/123456",
                location=location or "Remote",
                salary_raw="$120k – $160k",
                salary_min=120000,
                salary_max=160000,
                job_description=(
                    f"We are looking for a talented {keywords} Engineer to join our team. "
                    "You will work on cutting-edge technology, collaborate with cross-functional "
                    "teams, and help build scalable systems."
                ),
                requirements=[
                    f"5+ years of {keywords} experience",
                    "Strong problem-solving skills",
                    "Experience with cloud platforms (AWS / GCP / Azure)",
                    "Bachelor's degree in Computer Science or related field",
                ],
                skills_required=[keywords, "Python", "AWS", "Docker"],
                is_easy_apply=True,
                remote_type="remote",
                job_type="full-time",
                posted_at=datetime.utcnow(),
            )
            for _ in range(min(limit, 3))
        ]
        return stub_jobs

    async def get_details(self, job: RawJob) -> RawJob:
        """Enrich job with full description from job page. (stub)"""
        return job

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
