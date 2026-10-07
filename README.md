# Durable Multi-Agent Research Assistant

Portfolio project: a **bounded multi-agent research workflow** with durable SQLite checkpoints. Interrupt anytime and resume safely.

## Why this matters

Many “agents” are unbounded loops in memory. This project shows production-minded orchestration:

- Explicit states: `new → retrieved → synthesized → done`
- **step_budget** limits work per call
- SQLite checkpoints + compare-and-swap updates
- Job fingerprint binds `job_id` to query/context
- Model/synthesizer writes a memo — code owns tools and transitions

## Quick start

```bash
cd Durable-Multi-Agent-Research-Assistant

# Full run in one shot
python demo.py --run-all

# Or step-by-step (resume-friendly)
python demo.py --reset --step-budget 1
python demo.py --step-budget 1
python demo.py --step-budget 1
python demo.py --step-budget 1   # steps_this_call == 0 when done

python -m unittest discover -s tests -v
```

No third-party packages required (Python 3.10+).

## Agents (roles)

1. **Retriever agent** — TF-IDF search over tenant-scoped docs  
2. **Synthesis agent** — extractive memo from retrieved evidence  
3. **Finalize agent** — attach source IDs + human review status  

## Project layout

```text
data/documents.json
src/search.py
src/summary.py
src/agent.py          # durable state machine
demo.py
state/                # created at runtime (gitignored)
INTERVIEW_PREP.md
```

## Architecture

```text
Job ID + step budget
    → Load matching checkpoint (SQLite)
    → Retrieve evidence
    → Synthesize memo
    → Finalize sources
    → Compare-and-swap commit
```

## License

MIT — feel free to fork and extend.
