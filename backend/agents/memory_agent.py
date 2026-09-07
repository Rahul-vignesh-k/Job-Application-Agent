"""MemoryAgent — answer lookup (.env → SQLite → ChromaDB) and persistence."""
from __future__ import annotations
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.agents.schemas import (
    AgentName, AgentDecision,
    MemoryLookupInput, MemoryLookupOutput,
    MemorySaveInput, AuditInput,
)
from backend.agents.audit_agent import AuditAgent
from backend.config import get_settings
from backend.db import crud
from backend.rag.matcher import lookup_field_answer
from backend.rag.chromadb_client import upsert_document, COLLECTION_JOB_ANSWERS

settings = get_settings()
_audit = AuditAgent()

# Fields requiring user confirmation before auto-fill
_SENSITIVE_KEYS = frozenset([
    "expected_salary", "expected_ctc", "expected_stipend", "current_salary",
    "notice_period", "date_of_birth", "nationality", "gender",
    "disability", "criminal_record", "work_authorization",
])

# Pre-built env answer map (non-salary fields)
def _env_answers() -> dict[str, str]:
    s = settings
    return {
        "full_name": s.user_full_name,
        "email": s.user_email,
        "phone": s.user_phone,
        "location": s.user_location,
        "years_experience": str(s.user_years_experience),
        "notice_period": s.user_notice_period,
        "linkedin_url": s.user_linkedin_url,
        "github_url": s.user_github_url,
        "portfolio_url": s.user_portfolio_url or s.user_leetcode_url or s.user_github_url or s.user_linkedin_url,
        "leetcode_url": s.user_leetcode_url,
        "website": s.user_portfolio_url or s.user_leetcode_url or s.user_github_url or "",
        "coding_profile": s.user_leetcode_url or s.user_github_url or "",
    }


class MemoryAgent:
    name = AgentName.MEMORY

    async def lookup(self, db: AsyncSession, inp: MemoryLookupInput) -> MemoryLookupOutput:
        """
        Priority: .env → SQLite → ChromaDB semantic search.
        Sensitive fields always ask confirmation before auto-fill.
        """
        is_sensitive = inp.is_sensitive or inp.field_key in _SENSITIVE_KEYS

        # 1. env
        env = _env_answers()
        if inp.field_key in env and env[inp.field_key]:
            return MemoryLookupOutput(
                field_key=inp.field_key,
                answer=env[inp.field_key],
                confidence=1.0,
                source="env",
                needs_confirmation=is_sensitive,
                decision=AgentDecision.PROCEED,
                decision_reason="found_in_env",
            )

        # 2. SQLite
        sa = await crud.get_saved_answer(db, inp.field_key)
        if sa and sa.answer:
            return MemoryLookupOutput(
                field_key=inp.field_key,
                answer=sa.answer,
                confidence=float(sa.confidence),
                source="sqlite",
                needs_confirmation=is_sensitive,
                decision=AgentDecision.PROCEED,
                decision_reason="found_in_sqlite",
            )

        # 3. ChromaDB
        hit = await lookup_field_answer(inp.field_key, inp.field_label)
        if hit:
            return MemoryLookupOutput(
                field_key=inp.field_key,
                answer=hit["answer"],
                confidence=hit["confidence"],
                source="chromadb",
                needs_confirmation=is_sensitive or hit["confidence"] < 0.90,
                decision=AgentDecision.PROCEED,
                decision_reason=f"found_in_chromadb (conf={hit['confidence']})",
            )

        # Nothing found
        await _audit.log(db, AuditInput(
            agent_name=self.name, event="memory_miss",
            message=f"No answer found for field '{inp.field_key}' — needs manual input",
            decision=AgentDecision.AWAIT_APPROVAL,
            decision_reason="field_unknown",
        ))
        return MemoryLookupOutput(
            field_key=inp.field_key,
            answer=None,
            confidence=0.0,
            source="none",
            needs_confirmation=True,
            decision=AgentDecision.AWAIT_APPROVAL,
            decision_reason="field_unknown",
        )

    async def save(self, db: AsyncSession, inp: MemorySaveInput) -> None:
        """Persist a user-supplied answer to SQLite + ChromaDB."""
        await crud.upsert_saved_answer(
            db,
            inp.field_key,
            inp.answer,
            field_label=inp.field_label,
            is_sensitive=inp.is_sensitive,
            source="manual",
        )
        upsert_document(
            COLLECTION_JOB_ANSWERS,
            f"answer_{inp.field_key}",
            inp.answer,
            {"field_key": inp.field_key, "field_label": inp.field_label},
        )
        await _audit.log(db, AuditInput(
            agent_name=self.name, event="memory_saved",
            message=f"Saved answer for field '{inp.field_key}' (sensitive={inp.is_sensitive})",
            decision=AgentDecision.PROCEED,
            decision_reason="user_provided",
        ))
