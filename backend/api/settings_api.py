from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.config import get_settings

router = APIRouter(prefix="/settings", tags=["settings"])
settings = get_settings()


class ProfileUpdate(BaseModel):
    user_full_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    user_location: Optional[str] = None
    user_years_experience: Optional[int] = None
    user_current_salary: Optional[str] = None
    user_expected_salary_intern: Optional[str] = None
    user_expected_salary_fte: Optional[str] = None
    user_notice_period: Optional[str] = None
    user_linkedin_url: Optional[str] = None
    user_github_url: Optional[str] = None
    user_portfolio_url: Optional[str] = None
    user_leetcode_url: Optional[str] = None
    auto_apply_threshold: Optional[int] = None
    max_applications_per_day: Optional[int] = None


@router.get("")
async def get_settings_endpoint():
    s = get_settings()
    return {
        "user_full_name": s.user_full_name,
        "user_email": s.user_email,
        "user_phone": s.user_phone,
        "user_location": s.user_location,
        "user_years_experience": s.user_years_experience,
        "user_expected_salary_intern": s.user_expected_salary_intern,
        "user_expected_salary_fte": s.user_expected_salary_fte,
        "user_notice_period": s.user_notice_period,
        "user_linkedin_url": s.user_linkedin_url,
        "user_github_url": s.user_github_url,
        "user_portfolio_url": s.user_portfolio_url,
        "user_leetcode_url": s.user_leetcode_url,
        "auto_apply_threshold": s.auto_apply_threshold,
        "max_applications_per_day": s.max_applications_per_day,
        "gemini_model": s.gemini_model,
        "gemini_configured": bool(s.gemini_api_key),
    }


@router.patch("")
async def update_settings(payload: ProfileUpdate):
    # In production, persist to a settings DB table or .env file.
    # For now, update the in-memory singleton.
    s = get_settings()
    for field, value in payload.model_dump(exclude_none=True).items():
        if hasattr(s, field):
            object.__setattr__(s, field, value)
    return {"status": "updated"}
