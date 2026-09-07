"""
Job application state machine.

States and transitions:
  DISCOVERED → ANALYZING
  ANALYZING → MATCHED (score >= threshold) | REVIEW_REQUIRED (score < threshold) | FAILED
  MATCHED → APPLYING (user or auto)
  REVIEW_REQUIRED → TAILORING (user approves) | SKIPPED (user rejects)
  TAILORING → READY_TO_APPLY (tailor complete + user approves preview)
  READY_TO_APPLY → APPLYING
  APPLYING → APPLIED (success) | WAITING_INPUT (unknown field) | FAILED
  WAITING_INPUT → APPLYING (all fields resolved)
"""
from enum import Enum
from backend.db.models import JobStatus


class Event(str, Enum):
    START_ANALYSIS = "start_analysis"
    ANALYSIS_DONE = "analysis_done"
    APPROVE_APPLY = "approve_apply"
    APPROVE_TAILOR = "approve_tailor"
    TAILOR_DONE = "tailor_done"
    APPROVE_TAILORED = "approve_tailored"
    START_APPLY = "start_apply"
    UNKNOWN_FIELD = "unknown_field"
    FIELDS_RESOLVED = "fields_resolved"
    APPLY_SUCCESS = "apply_success"
    APPLY_FAILED = "apply_failed"
    SKIP = "skip"
    RESET = "reset"


TRANSITIONS: dict[tuple[JobStatus, Event], JobStatus] = {
    (JobStatus.DISCOVERED, Event.START_ANALYSIS): JobStatus.ANALYZING,
    (JobStatus.ANALYZING, Event.ANALYSIS_DONE): JobStatus.REVIEW_REQUIRED,      # default; agent overrides to MATCHED
    (JobStatus.ANALYZING, Event.APPLY_FAILED): JobStatus.FAILED,
    (JobStatus.REVIEW_REQUIRED, Event.APPROVE_APPLY): JobStatus.READY_TO_APPLY,
    (JobStatus.REVIEW_REQUIRED, Event.APPROVE_TAILOR): JobStatus.TAILORING,
    (JobStatus.REVIEW_REQUIRED, Event.SKIP): JobStatus.SKIPPED,
    (JobStatus.TAILORING, Event.TAILOR_DONE): JobStatus.TAILORING,              # waiting for preview approval
    (JobStatus.TAILORING, Event.APPROVE_TAILORED): JobStatus.READY_TO_APPLY,
    (JobStatus.TAILORING, Event.SKIP): JobStatus.SKIPPED,
    (JobStatus.READY_TO_APPLY, Event.START_APPLY): JobStatus.APPLYING,
    (JobStatus.APPLYING, Event.UNKNOWN_FIELD): JobStatus.WAITING_INPUT,
    (JobStatus.APPLYING, Event.APPLY_SUCCESS): JobStatus.APPLIED,
    (JobStatus.APPLYING, Event.APPLY_FAILED): JobStatus.FAILED,
    (JobStatus.WAITING_INPUT, Event.FIELDS_RESOLVED): JobStatus.APPLYING,
    (JobStatus.WAITING_INPUT, Event.SKIP): JobStatus.SKIPPED,
    # allow retry from failed
    (JobStatus.FAILED, Event.RESET): JobStatus.DISCOVERED,
}


def transition(current: JobStatus, event: Event) -> JobStatus | None:
    """Return new status or None if the transition is invalid."""
    return TRANSITIONS.get((current, event))
