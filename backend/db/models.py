from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Boolean, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from backend.db.database import Base


class JobStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    ANALYZING = "analyzing"
    REVIEW_REQUIRED = "review_required"
    TAILORING = "tailoring"
    WAITING_INPUT = "waiting_input"
    READY_TO_APPLY = "ready_to_apply"
    APPLYING = "applying"
    APPLIED = "applied"
    FAILED = "failed"
    SKIPPED = "skipped"
    REJECTED = "rejected"
    INTERVIEW = "interview"


class ApplicationResult(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"


class Platform(str, enum.Enum):
    LINKEDIN = "linkedin"
    NAUKRI = "naukri"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    MANUAL = "manual"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    platform = Column(SAEnum(Platform), nullable=False)
    location = Column(String)
    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_currency = Column(String, default="USD")
    salary_raw = Column(String)
    job_description = Column(Text)
    requirements = Column(JSON)          # list of strings
    skills_required = Column(JSON)       # list of strings
    apply_url = Column(String)
    external_id = Column(String)         # platform-specific job ID
    status = Column(SAEnum(JobStatus), default=JobStatus.DISCOVERED)
    match_score = Column(Float)
    match_details = Column(JSON)         # detailed gap analysis
    is_easy_apply = Column(Boolean, default=False)
    remote_type = Column(String)         # remote / hybrid / onsite
    job_type = Column(String)            # full-time / part-time / contract (connector-provided)
    job_classification = Column(String)  # AI-classified: "Internship" | "FTE" | None
    posted_at = Column(DateTime(timezone=True))
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    notes = Column(Text)

    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    pending_fields = relationship("PendingFormField", back_populates="job", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True)
    version = Column(String, nullable=False)    # "base" | "tailored_<job_id>"
    file_path = Column(String, nullable=False)
    content_text = Column(Text)                 # extracted plain text
    is_base = Column(Boolean, default=False)
    tailored_for_job = Column(String, ForeignKey("jobs.id"), nullable=True)
    diff_summary = Column(Text)                 # AI-generated summary of changes vs base
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    applications = relationship("Application", back_populates="resume")


class Application(Base):
    __tablename__ = "applications"

    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=True)
    status = Column(SAEnum(JobStatus), default=JobStatus.APPLYING)
    result = Column(SAEnum(ApplicationResult), default=ApplicationResult.PENDING)
    applied_at = Column(DateTime(timezone=True))
    confirmation_number = Column(String)
    screenshot_path = Column(String)
    error_message = Column(Text)
    form_data_used = Column(JSON)               # snapshot of what was submitted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")


class SavedAnswer(Base):
    """Persistent store for manual answers to job-application form fields."""
    __tablename__ = "saved_answers"

    id = Column(String, primary_key=True)
    field_key = Column(String, nullable=False, index=True)   # normalised field name
    field_label = Column(String)                              # human-readable label
    answer = Column(Text, nullable=False)
    is_sensitive = Column(Boolean, default=False)            # salary / legal / etc.
    confidence = Column(Float, default=1.0)
    source = Column(String, default="manual")                # manual | env | chromadb
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class PendingFormField(Base):
    """Fields that appeared during automation and could not be auto-filled."""
    __tablename__ = "pending_form_fields"

    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    field_key = Column(String, nullable=False)
    field_label = Column(String)
    field_type = Column(String, default="text")   # text | select | checkbox | radio
    options = Column(JSON)                        # for select/radio
    is_resolved = Column(Boolean, default=False)
    answer = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="pending_fields")


class AgentLog(Base):
    """Audit trail for every agent action."""
    __tablename__ = "agent_logs"

    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=True)
    event = Column(String, nullable=False)
    level = Column(String, default="info")    # info | warning | error
    message = Column(Text)
    extra = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
