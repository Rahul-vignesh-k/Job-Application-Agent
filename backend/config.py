from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from functools import lru_cache
import os


class Settings(BaseSettings):
    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    secret_key: str = "dev_secret_key_change_in_prod"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    chroma_persist_dir: str = "./data/chroma"

    # Resume
    resume_upload_dir: str = "./uploads/resumes"
    default_resume_path: str = "./uploads/resumes/base_resume.pdf"

    # Job sources
    linkedin_email: str = ""
    linkedin_password: str = ""
    naukri_email: str = ""
    naukri_password: str = ""
    indeed_email: str = ""
    indeed_password: str = ""

    # Auto-apply
    auto_apply_threshold: int = 85
    max_applications_per_day: int = 20
    apply_delay_seconds: int = 5

    # User profile
    user_full_name: str = ""
    user_email: str = ""
    user_phone: str = ""
    user_location: str = ""
    user_years_experience: int = 0
    user_current_salary: str = ""
    user_expected_salary_intern: str = ""
    user_expected_salary_fte: str = ""
    user_notice_period: str = "Immediate"
    user_linkedin_url: str = ""
    user_github_url: str = ""
    user_portfolio_url: str = ""
    user_leetcode_url: str = ""

    # CORS
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def ensure_dirs(self):
        Path(self.resume_upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        Path("./data").mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s
