"""Tests for durable multi-agent research assistant."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent import run_job

DOCS = ROOT / "data" / "documents.json"


class ResearchAgentTests(unittest.TestCase):
    def test_stepwise_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "state.sqlite3"
            request = {
                "job_id": "research-1",
                "query": "How do evaluation and deployment improve RAG?",
                "documents_path": DOCS,
                "state_db": db,
                "step_budget": 1,
            }
            self.assertEqual(run_job(**request)["state"], "retrieved")
            self.assertEqual(run_job(**request)["state"], "synthesized")
            done = run_job(**request)
            self.assertEqual(done["state"], "done")
            self.assertEqual(len(done["trace"]), 3)
            self.assertEqual(run_job(**request)["steps_this_call"], 0)

    def test_fingerprint_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "state.sqlite3"
            run_job(
                job_id="research-1",
                query="How do evaluation and deployment improve RAG?",
                documents_path=DOCS,
                state_db=db,
                step_budget=1,
            )
            with self.assertRaises(ValueError):
                run_job(
                    job_id="research-1",
                    query="Different query same job id",
                    documents_path=DOCS,
                    state_db=db,
                    step_budget=1,
                )


if __name__ == "__main__":
    unittest.main()
