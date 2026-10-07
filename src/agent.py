"""Bounded multi-step research workflow with durable SQLite checkpoints."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .search import Search
from .summary import extractive_summary

STATES = ("new", "retrieved", "synthesized", "done")


def digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


@contextmanager
def database(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def run_job(
    *,
    job_id: str,
    query: str,
    documents_path: Path,
    state_db: Path,
    step_budget: int = 3,
    tenant: str = "A",
    backend: str = "local",
    model: str = "local-extractive",
) -> dict:
    if not isinstance(job_id, str) or not job_id.strip():
        raise ValueError("job_id must be a nonempty string")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a nonempty string")
    if type(step_budget) is not int or not 1 <= step_budget <= 3:
        raise ValueError("step_budget must be 1 through 3")

    fingerprint = digest([query, tenant, backend, model])
    with database(state_db) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS jobs ("
            "id TEXT PRIMARY KEY, fingerprint TEXT, state TEXT, value TEXT)"
        )
        old = connection.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if old and old["fingerprint"] != fingerprint:
            raise ValueError("job ID is bound to different query or execution context")
        if old:
            state, value = old["state"], json.loads(old["value"])
        else:
            state, value = "new", {"query": query, "trace": []}
            connection.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?)",
                (job_id, fingerprint, state, json.dumps(value)),
            )

    completed_now = 0
    while state != "done" and completed_now < step_budget:
        if state == "new":
            docs = [
                doc
                for doc in json.loads(documents_path.read_text(encoding="utf-8"))
                if doc["tenant"] == tenant
            ]
            value["evidence"] = Search(docs).query(query, 4)
            state = "retrieved"
        elif state == "retrieved":
            source = " ".join(doc["text"] for doc in value.get("evidence", []))
            if not source:
                value["answer"] = "No evidence available."
            else:
                value["answer"] = extractive_summary(source, 4)
            state = "synthesized"
        else:
            value["sources"] = [doc["id"] for doc in value.get("evidence", [])]
            value["support_status"] = "human evidence review required"
            state = "done"

        value["trace"].append(state)
        prior = (
            "new"
            if state == "retrieved"
            else ("retrieved" if state == "synthesized" else "synthesized")
        )
        with database(state_db) as connection:
            updated = connection.execute(
                "UPDATE jobs SET state=?, value=? WHERE id=? AND state=?",
                (state, json.dumps(value), job_id, prior),
            )
            if updated.rowcount != 1:
                raise RuntimeError(
                    "concurrent worker advanced this job; resume to reload"
                )
        completed_now += 1

    return {
        **value,
        "job_id": job_id,
        "state": state,
        "steps_this_call": completed_now,
        "execution": "bounded workflow; synthesizer writes memo, not arbitrary tool code",
        "agents": [
            "retriever-agent (search evidence)",
            "synthesis-agent (write memo from evidence)",
            "finalize-agent (attach sources + review status)",
        ],
    }
