"""Pydantic schemas shared across all specialist agents."""
from __future__ import annotations
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from enum import Enum


class AgentName(str, Enum):
    SUPERVISOR      = "SupervisorAgent"
    SOURCING        = "SourcingAgent"
    JOB_ANALYSIS   = "JobAnalysisAgent"
    RESUME_TAILOR  = "ResumeTailorAgent"
    APPLICATION    = "ApplicationAgent"
    MEMORY         = "MemoryAgent"
    AUDIT          = "AuditAgent"


class AgentDecision(str, Enum):
    PROCEED         = "proceed"
    AWAIT_APPROVAL  = "await_approval"
    SKIP            = "skip"
    FAIL            = "fail"
    ROUTE           = "route"


# ── Sourcing ────────────────────────────────────────────────────────────────

class SourcingInput(BaseModel):
    keywords: str
    location: str = ""
    platforms: List[str] = ["linkedin", "naukri", "indeed", "glassdoor"]
    limit: int = 20


class SourcingOutput(BaseModel):
    jobs_found: int
    job_ids: List[str]
    skipped_platforms: List[str] = []
    failed_platforms: List[str] = []


# ── Job Analysis ─────────────────────────────────────────────────────────────

class GapItem(BaseModel):
    category: str
    gap: str
    severity: str  # critical | moderate | minor
    suggestion: str


class JobAnalysisInput(BaseModel):
    job_id: str


class JobAnalysisOutput(BaseModel):
    job_id: str
    job_classification: str          # Internship | FTE
    match_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    gaps: List[GapItem]
    overall_summary: str
    recommendation: str              # auto_apply | review_required | skip
    decision: AgentDecision
    decision_reason: str


# ── Resume Tailor ─────────────────────────────────────────────────────────────

class ResumeTailorInput(BaseModel):
    job_id: str
    resume_id: Optional[str] = None  # None = use base resume


class ResumeTailorOutput(BaseModel):
    job_id: str
    tailored_resume_id: str
    tailored_text: str
    diff_summary: str
    decision: AgentDecision
    decision_reason: str


# ── Application ───────────────────────────────────────────────────────────────

class ApplicationInput(BaseModel):
    job_id: str
    resume_id: Optional[str] = None


class ApplicationOutput(BaseModel):
    job_id: str
    success: bool
    confirmation_number: Optional[str] = None
    screenshot_path: Optional[str] = None
    error: Optional[str] = None
    unknown_fields: List[dict] = []
    decision: AgentDecision
    decision_reason: str


# ── Memory ────────────────────────────────────────────────────────────────────

class MemoryLookupInput(BaseModel):
    field_key: str
    field_label: str
    is_sensitive: bool = False


class MemoryLookupOutput(BaseModel):
    field_key: str
    answer: Optional[str] = None
    confidence: float = 0.0
    source: str = "none"           # env | sqlite | chromadb | none
    needs_confirmation: bool = False
    decision: AgentDecision
    decision_reason: str


class MemorySaveInput(BaseModel):
    field_key: str
    field_label: str
    answer: str
    is_sensitive: bool = False


# ── Audit ─────────────────────────────────────────────────────────────────────

class AuditInput(BaseModel):
    agent_name: AgentName
    event: str
    job_id: Optional[str] = None
    level: str = "info"
    message: str
    decision: Optional[AgentDecision] = None
    decision_reason: Optional[str] = None
    extra: Optional[dict] = None


# ── Supervisor ────────────────────────────────────────────────────────────────

class SupervisorState(str, Enum):
    IDLE            = "idle"
    SOURCING        = "sourcing"
    ANALYSING       = "analysing"
    AWAITING_TAILOR = "awaiting_tailor"
    TAILORING       = "tailoring"
    AWAITING_APPLY  = "awaiting_apply"
    APPLYING        = "applying"
    AWAITING_INPUT  = "awaiting_input"
    DONE            = "done"
    FAILED          = "failed"
