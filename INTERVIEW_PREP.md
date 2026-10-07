# Interview prep — Durable Multi-Agent Research Assistant

## 60-second pitch

I built a durable multi-agent research assistant. Instead of an unbounded agent loop, code owns a state machine (`retrieve → synthesize → finalize`) with SQLite checkpoints and compare-and-swap updates. You can stop after any step, restart the process, and resume without redoing finished work. The synthesizer writes the memo; it does not execute arbitrary tools.

## Live demo commands

```bash
python demo.py --reset --step-budget 1   # -> retrieved
python demo.py --step-budget 1           # -> synthesized
python demo.py --step-budget 1           # -> done
python demo.py --step-budget 1           # steps_this_call=0
python demo.py --run-all
```

## Architecture talking points

- **Durable** = committed state + working value survive process restart.
- **Compare-and-swap** prevents stale workers from overwriting newer checkpoints.
- **Fingerprint** rejects reusing a job ID with a different query/backend.
- This is a **bounded workflow**, not fully autonomous tool-calling agent.

## Likely interview Q&A

**Q: What makes the workflow durable?**  
A: Each completed state is committed to SQLite with the working payload (evidence/answer/trace). A new process reloads and continues.

**Q: Does checkpointing guarantee exactly-once LLM calls?**  
A: No. Crash after generation but before commit can repeat the model call. Exactly-once across systems needs idempotency keys / outbox patterns.

**Q: Why compare-and-swap?**  
A: Update only if stored prior state still matches what this worker expects. Concurrent progress cannot be silently overwritten.

**Q: Is this an autonomous agent?**  
A: It is multi-role orchestration with fixed steps. Great foundation before adding risky open-ended planners.

**Q: What if the corpus changes mid-job?**  
A: This design snapshots evidence at retrieve time. For fresh research, start a new job_id.

## Tie-back to your Data Dynamics work

At work you’re extending PII detection with multi-agent flows (detect → validate → risk → explain). This project shows you understand **durable orchestration, trust boundaries, and resumability** — the same production concerns, in a clean portfolio demo.

## Production next steps

Queue + leases, retries with classification, deadlines/cancellation, model-call IDs, source revision tracking, optional Ollama generation behind the same validation boundary.
