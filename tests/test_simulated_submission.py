"""Regression checks for demo submission boundaries, with no browser or database.

Real adapter, orchestration methods, output schemas and audit wrapper are loaded.
Only external dependency modules and persistence calls are substituted. This lets
the honesty regression run without installing Chroma, Gemini or Playwright.
"""
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch


ROOT = Path(__file__).resolve().parents[1]


def module(name, **attributes):
    value = ModuleType(name)
    value.__dict__.update(attributes)
    return value


def load_source(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


class SimulationBoundaryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.crud = module("backend.db.crud", **{
            name: AsyncMock() for name in (
                "get_job", "log_event", "create_application", "update_application",
                "update_job_status", "get_base_resume", "list_pending_fields",
                "list_saved_answers",
            )
        })
        self.crud.get_job.return_value = SimpleNamespace(id="job-1")
        substitutes = {
            "sqlalchemy": module("sqlalchemy"),
            "sqlalchemy.ext": module("sqlalchemy.ext"),
            "sqlalchemy.ext.asyncio": module("sqlalchemy.ext.asyncio", AsyncSession=object),
            "backend.agents": module("backend.agents", __path__=[str(ROOT / "backend/agents")]),
            "backend.config": module("backend.config", get_settings=lambda: SimpleNamespace()),
            "backend.db": module("backend.db", crud=self.crud),
            "backend.db.crud": self.crud,
            "backend.db.models": module("backend.db.models", JobStatus=Mock(), ApplicationResult=Mock()),
            "backend.agent.state_machine": module("backend.agent.state_machine", Event=Mock(), transition=Mock()),
            "backend.mcp": module("backend.mcp", CONNECTORS={}),
            "backend.mcp.base": module("backend.mcp.base", RawJob=object),
            "backend.rag.matcher": module("backend.rag.matcher", **{
                name: AsyncMock() for name in ("match_resume_to_jd", "tailor_resume", "classify_job_type")
            }),
            "backend.resumes.resume_processor": module("backend.resumes.resume_processor", extract_text=Mock()),
            "backend.rag.chromadb_client": module(
                "backend.rag.chromadb_client", upsert_document=Mock(), COLLECTION_JOB_ANSWERS="test"
            ),
        }
        self.modules_patch = patch.dict(sys.modules, substitutes)
        self.modules_patch.start()
        self.addCleanup(self.modules_patch.stop)
        self.adapter = load_source("backend.automation.applicator", "backend/automation/applicator.py")
        self.schemas = load_source("backend.agents.schemas", "backend/agents/schemas.py")
        load_source("backend.agents.audit_agent", "backend/agents/audit_agent.py")
        self.specialist = load_source("backend.agents.application_agent", "backend/agents/application_agent.py")
        self.legacy = load_source("backend.agent.job_agent", "backend/agent/job_agent.py")

    def assert_no_submission_record(self):
        self.crud.create_application.assert_not_awaited()
        self.crud.update_application.assert_not_awaited()
        self.crud.update_job_status.assert_not_awaited()
        self.crud.get_base_resume.assert_not_awaited()
        self.crud.log_event.assert_awaited_once()
        call = self.crud.log_event.await_args
        event = call.kwargs.get("event", call.args[1] if len(call.args) > 1 else None)
        self.assertEqual(event, "application_not_submitted")
        self.assertTrue(call.kwargs["metadata"]["simulated"])

    async def test_placeholder_never_returns_a_submission_or_opens_a_browser(self):
        with patch("socket.socket", side_effect=AssertionError("No network allowed")):
            result = await self.adapter.JobApplicator().apply(
                "https://example.invalid/application", "missing-resume.pdf", {}, "job-1"
            )
        self.assertIs(result["success"], False)
        self.assertEqual(result["submission_status"], "not_submitted")
        self.assertIs(result["simulated"], True)
        self.assertIsNone(result["confirmation"])
        self.assertIsNone(result["screenshot"])

    async def test_specialist_preserves_job_and_application_counts_for_demo(self):
        output = await self.specialist.ApplicationAgent().run(
            object(), self.schemas.ApplicationInput(job_id="job-1")
        )
        self.assertFalse(output.success)
        self.assertEqual(output.submission_status, "not_submitted")
        self.assertTrue(output.simulated)
        self.assertIsNone(output.confirmation_number)
        self.assertEqual(output.decision, self.schemas.AgentDecision.SKIP)
        self.assert_no_submission_record()

    async def test_legacy_agent_preserves_job_and_application_counts_for_demo(self):
        result = await self.legacy.JobAgent().submit_application(object(), "job-1")
        self.assertFalse(result["success"])
        self.assertEqual(result["submission_status"], "not_submitted")
        self.assertTrue(result["simulated"])
        self.assertIsNone(result["confirmation"])
        self.assert_no_submission_record()

    async def test_adapter_without_explicit_submission_capability_is_blocked(self):
        unexpected_adapter = SimpleNamespace(apply=AsyncMock(return_value={"success": True}))
        with patch.object(self.specialist, "get_applicator", return_value=unexpected_adapter):
            output = await self.specialist.ApplicationAgent().run(
                object(), self.schemas.ApplicationInput(job_id="job-1")
            )
        self.assertFalse(output.success)
        unexpected_adapter.apply.assert_not_awaited()
        self.assert_no_submission_record()


if __name__ == "__main__":
    unittest.main()
