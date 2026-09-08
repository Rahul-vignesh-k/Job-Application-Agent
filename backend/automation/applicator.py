"""Application adapter placeholder; no live submission is implemented yet."""
from typing import Optional


NOT_SUBMITTED_MESSAGE = (
    "Application submission is not implemented. This is a simulation; "
    "no application was submitted."
)


def not_submitted_result() -> dict:
    """Return a non-submission without inventing confirmation evidence."""
    return {
        "success": False,
        "submission_status": "not_submitted",
        "simulated": True,
        "screenshot": None,
        "confirmation": None,
        "error": NOT_SUBMITTED_MESSAGE,
    }


class ApplicationError(Exception):
    pass


class UnknownFieldError(Exception):
    """Raised when the form contains a field the agent cannot auto-fill."""
    def __init__(self, field_key: str, field_label: str, field_type: str = "text", options: list = None):
        self.field_key = field_key
        self.field_label = field_label
        self.field_type = field_type
        self.options = options or []
        super().__init__(f"Unknown field: {field_label}")


class JobApplicator:
    """Fail closed until a real adapter can provide external submission evidence."""

    supports_submission = False

    async def apply(self, apply_url: str, resume_path: str, form_data: dict, job_id: str) -> dict:
        # Opening a page or taking a screenshot cannot prove a submission.
        # The placeholder performs no browser action and creates no confirmation.
        return not_submitted_result()

    async def close(self):
        pass


_applicator: Optional[JobApplicator] = None


def get_applicator() -> JobApplicator:
    global _applicator
    if _applicator is None:
        _applicator = JobApplicator()
    return _applicator
