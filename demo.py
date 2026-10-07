"""End-to-end demo for Durable Multi-Agent Research Assistant."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.agent import run_job

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "data" / "documents.json"
DB = ROOT / "state" / "research.sqlite3"


def main() -> None:
    parser = argparse.ArgumentParser(description="Durable research agent demo")
    parser.add_argument("--job-id", default="research-1")
    parser.add_argument(
        "--query",
        default="How do evaluation and deployment improve RAG?",
    )
    parser.add_argument("--step-budget", type=int, default=1)
    parser.add_argument("--reset", action="store_true", help="Delete local SQLite state")
    parser.add_argument("--run-all", action="store_true", help="Run until done in one process")
    args = parser.parse_args()

    if args.reset and DB.exists():
        DB.unlink()
        print(f"Reset state database: {DB}")

    if args.run_all:
        if DB.exists():
            DB.unlink()
        result = run_job(
            job_id=args.job_id,
            query=args.query,
            documents_path=DOCS,
            state_db=DB,
            step_budget=3,
        )
        print(json.dumps(result, indent=2))
        return

    result = run_job(
        job_id=args.job_id,
        query=args.query,
        documents_path=DOCS,
        state_db=DB,
        step_budget=args.step_budget,
    )
    print(json.dumps(result, indent=2))
    print()
    print(
        f"state={result['state']} steps_this_call={result['steps_this_call']} "
        f"trace={result.get('trace')}"
    )
    if result["state"] != "done":
        print("Tip: run the same command again to resume the next durable step.")


if __name__ == "__main__":
    main()
