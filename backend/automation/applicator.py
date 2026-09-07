"""Playwright-based form automation for job applications."""
import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PWTimeout

from backend.config import get_settings
from backend.db.models import JobStatus

settings = get_settings()

SCREENSHOTS_DIR = "./data/screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


class ApplicationError(Exception):
    pass


class UnknownFieldError(Exception):
    """Raised when the form contains a field the agent can't auto-fill."""
    def __init__(self, field_key: str, field_label: str, field_type: str = "text", options: list = None):
        self.field_key = field_key
        self.field_label = field_label
        self.field_type = field_type
        self.options = options or []
        super().__init__(f"Unknown field: {field_label}")


class JobApplicator:
    """Drives a Playwright browser to fill and submit job applications."""

    def __init__(self):
        self._browser: Optional[Browser] = None

    async def _ensure_browser(self):
        if self._browser is None:
            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )

    async def apply(
        self,
        apply_url: str,
        resume_path: str,
        form_data: dict,
        job_id: str,
    ) -> dict:
        """
        Navigate to apply_url and attempt to fill the application form.

        Returns:
            {"success": bool, "screenshot": str, "confirmation": str, "error": str}
        Raises:
            UnknownFieldError if an unknown field is encountered.
        """
        await self._ensure_browser()
        context = await self._browser.new_context()
        page = await context.new_page()
        screenshot_path = f"{SCREENSHOTS_DIR}/{job_id}_{uuid.uuid4().hex[:6]}.png"

        try:
            await page.goto(apply_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(settings.apply_delay_seconds)

            # ── STUB: Real form logic goes here ──────────────────────────────
            # In a real implementation you would:
            # 1. Detect the form framework (Workday, Greenhouse, Lever, etc.)
            # 2. Fill each field using form_data mappings
            # 3. Upload the resume file
            # 4. Check for unknown fields → raise UnknownFieldError
            # 5. Submit and capture confirmation
            # ─────────────────────────────────────────────────────────────────

            await page.screenshot(path=screenshot_path, full_page=True)
            return {
                "success": True,
                "screenshot": screenshot_path,
                "confirmation": f"stub_confirm_{uuid.uuid4().hex[:8]}",
                "error": None,
            }
        except PWTimeout as e:
            await page.screenshot(path=screenshot_path, full_page=True)
            return {
                "success": False,
                "screenshot": screenshot_path,
                "confirmation": None,
                "error": f"Timeout: {str(e)}",
            }
        except UnknownFieldError:
            raise
        except Exception as e:
            return {
                "success": False,
                "screenshot": screenshot_path,
                "confirmation": None,
                "error": str(e),
            }
        finally:
            await context.close()

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None


# Module-level singleton
_applicator: Optional[JobApplicator] = None


def get_applicator() -> JobApplicator:
    global _applicator
    if _applicator is None:
        _applicator = JobApplicator()
    return _applicator
