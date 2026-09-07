"""Gemini + ChromaDB powered resume ↔ JD matcher and resume tailor."""
import json
import re
from typing import Optional
import google.generativeai as genai

from backend.config import get_settings
from backend.rag.chromadb_client import query_similar, upsert_document, COLLECTION_RESUMES, COLLECTION_JD

settings = get_settings()

if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)


def _model():
    return genai.GenerativeModel(settings.gemini_model)


MATCH_PROMPT = """You are an expert ATS and technical recruiter AI.

Given:
- RESUME TEXT (candidate's resume)
- JOB DESCRIPTION (target role)
- SIMILAR EXPERIENCE SNIPPETS from the candidate's past applications (ChromaDB RAG context)

Your task:
1. Analyse how well the resume matches the job description.
2. Return a JSON object with the exact schema below. No markdown, no extra text.

Schema:
{{
  "match_score": <int 0-100>,
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "matched_experience": ["phrase from resume"],
  "gaps": [
    {{
      "category": "Technical Skills | Experience | Education | Soft Skills | Certification",
      "gap": "description of gap",
      "severity": "critical | moderate | minor",
      "suggestion": "how to address"
    }}
  ],
  "overall_summary": "2-3 sentence summary",
  "recommendation": "auto_apply | review_required | skip"
}}

RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}

RAG CONTEXT (similar past experience):
{rag_context}
"""

TAILOR_PROMPT = """You are a professional resume writer with 20 years of experience.

Given a base resume and a target job description, rewrite the resume to:
1. Highlight the most relevant skills and experiences for THIS specific role.
2. Mirror the language and keywords from the job description (for ATS optimisation).
3. Quantify achievements where possible.
4. Keep all information truthful — do not fabricate experience.
5. Maintain the same general structure and length.

Return ONLY the tailored resume text. No commentary.

BASE RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}

GAPS TO ADDRESS:
{gaps_json}
"""


async def match_resume_to_jd(resume_text: str, jd_text: str, job_id: str) -> dict:
    """Return match analysis dict with score, gaps, etc."""
    # Fetch RAG context: similar resume sections
    rag_hits = query_similar(COLLECTION_RESUMES, jd_text[:1000], n_results=3)
    rag_context = "\n\n---\n\n".join(h["text"] for h in rag_hits) if rag_hits else "None available."

    # Cache JD in ChromaDB for future reference
    upsert_document(COLLECTION_JD, job_id, jd_text, {"job_id": job_id})

    prompt = MATCH_PROMPT.format(
        resume_text=resume_text[:6000],
        jd_text=jd_text[:3000],
        rag_context=rag_context[:2000],
    )

    try:
        model = _model()
        response = model.generate_content(prompt)
        raw = response.text.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        result = json.loads(raw)
        return result
    except Exception as e:
        # Return a safe fallback so the agent can continue
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "matched_experience": [],
            "gaps": [],
            "overall_summary": f"Analysis failed: {str(e)}",
            "recommendation": "review_required",
            "error": str(e),
        }


async def tailor_resume(resume_text: str, jd_text: str, gaps: list) -> str:
    """Return tailored resume as plain text."""
    prompt = TAILOR_PROMPT.format(
        resume_text=resume_text[:6000],
        jd_text=jd_text[:3000],
        gaps_json=json.dumps(gaps, indent=2),
    )
    try:
        model = _model()
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[Tailoring failed: {e}]\n\n{resume_text}"


_INTERN_KEYWORDS = frozenset([
    "intern", "internship", "trainee", "student", "apprentice",
    "co-op", "coop", "summer program", "graduate trainee",
])
_FTE_KEYWORDS = frozenset([
    "full-time", "full time", "fte", "permanent", "associate",
    "software engineer", "software developer", "developer", "engineer",
    "sde", "swe", "senior", "lead", "staff", "principal",
])

_CLASSIFY_PROMPT = """Classify this job as exactly one of: "Internship" or "FTE".

Rules:
- Internship: contains intern/internship/trainee/student/co-op/graduate trainee
- FTE: full-time/permanent/associate/software engineer/developer
- When in doubt, output "FTE"

Return ONLY the single word "Internship" or "FTE". No explanation.

JOB TITLE: {title}
JOB DESCRIPTION (first 500 chars): {jd_snippet}
"""


async def classify_job_type(title: str, jd_text: str) -> str:
    """
    Classify job as 'Internship' or 'FTE'.
    Priority: keyword match → Gemini → default 'FTE'.
    """
    combined = (title + " " + jd_text[:300]).lower()

    # Fast keyword pass
    if any(kw in combined for kw in _INTERN_KEYWORDS):
        return "Internship"
    if any(kw in combined for kw in _FTE_KEYWORDS):
        return "FTE"

    # Ambiguous — ask Gemini
    if not settings.gemini_api_key:
        return "FTE"  # safe default when no AI available
    try:
        prompt = _CLASSIFY_PROMPT.format(title=title, jd_snippet=jd_text[:500])
        model = _model()
        response = model.generate_content(prompt)
        result = response.text.strip().strip('"').strip("'")
        if result in ("Internship", "FTE"):
            return result
    except Exception:
        pass
    return "FTE"  # safe default


async def lookup_field_answer(field_key: str, field_label: str, context: str = "") -> Optional[dict]:
    """
    Try to find a high-confidence answer for an unknown form field.
    Returns {"answer": str, "confidence": float, "source": str} or None.
    """
    from backend.rag.chromadb_client import COLLECTION_JOB_ANSWERS
    query = f"form field: {field_label} {field_key} {context}"
    hits = query_similar(COLLECTION_JOB_ANSWERS, query, n_results=3)
    if not hits:
        return None
    best = hits[0]
    confidence = max(0.0, 1.0 - best["distance"])
    if confidence >= 0.75:
        return {
            "answer": best["text"],
            "confidence": round(confidence, 3),
            "source": "chromadb",
            "metadata": best["metadata"],
        }
    return None
