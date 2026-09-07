"""Base class for all job-source MCP connectors."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class RawJob:
    """Normalised job record returned by any connector."""
    external_id: str
    title: str
    company: str
    platform: str
    apply_url: str
    location: str = ""
    salary_raw: str = ""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    job_description: str = ""
    requirements: list = field(default_factory=list)
    skills_required: list = field(default_factory=list)
    is_easy_apply: bool = False
    remote_type: str = ""
    job_type: str = "full-time"
    posted_at: Optional[datetime] = None


class BaseConnector(ABC):
    """All connectors must implement `search` and `get_details`."""

    platform: str = "unknown"

    @abstractmethod
    async def search(self, keywords: str, location: str = "", limit: int = 20) -> list[RawJob]:
        """Search for jobs matching keywords."""
        ...

    @abstractmethod
    async def get_details(self, job: RawJob) -> RawJob:
        """Enrich a RawJob with full description/requirements."""
        ...

    async def close(self):
        """Clean up resources (browser, sessions)."""
        pass
