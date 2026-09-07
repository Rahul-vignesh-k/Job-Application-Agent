"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List


class DiscoverRequest(BaseModel):
    keywords: str = Field(..., min_length=1, description="Job search keywords")
    location: str = Field(default="", description="Target location")
    platforms: List[str] = Field(default=["linkedin", "naukri", "indeed", "glassdoor"])
    limit: int = Field(default=20, ge=1, le=100)


class AnalyseResponse(BaseModel):
    match_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    matched_experience: List[str]
    gaps: List[dict]
    overall_summary: str
    recommendation: str


class ResolveFieldsRequest(BaseModel):
    answers: dict = Field(..., description="Mapping of {field_id: answer_string}")


class SaveAnswerRequest(BaseModel):
    field_key: str
    field_label: Optional[str] = None
    answer: str
    is_sensitive: bool = False


class SettingsUpdateRequest(BaseModel):
    user_full_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    user_location: Optional[str] = None
    user_years_experience: Optional[int] = None
    user_expected_salary: Optional[str] = None
    user_notice_period: Optional[str] = None
    user_linkedin_url: Optional[str] = None
    user_github_url: Optional[str] = None
    user_portfolio_url: Optional[str] = None
    auto_apply_threshold: Optional[int] = Field(None, ge=50, le=100)
    max_applications_per_day: Optional[int] = Field(None, ge=1, le=200)
