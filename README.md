# Northern Coast lead scoring

[Live POST endpoint](https://northerncoast-service.vercel.app/api/score) ·
[API explorer](https://northerncoast-service.vercel.app/docs) ·
[Source](https://github.com/larry-pult/northerncoast-service)

**Time spent: 83 minutes (1 hour 23 minutes).**

`POST /api/score` accepts a conversation transcript and returns its lead ID,
score, tier, routing, and a 1–2 sentence rationale.

**Approach:** one zero-shot OpenAI Responses call using `gpt-6-luna`, chosen for
this bounded, cost-sensitive classification task. Structured Outputs and
Pydantic validate the contract; the application preserves the lead ID.

**Rubric:** volume 35 points, business credibility 25, product fit 20, readiness
20. Volume leads because Northern Coast sells container loads. Hot starts at
80; Warm at 40. License claims are soft evidence. Routing selects the next
action, so an actionable Warm lead can receive a KAM handoff.

**Reliability:** configurable ten-second model deadline, no retries. Invalid
input returns 422; provider/output failures 502; provider throttling 503;
deadline expiration 504. Failures never produce fabricated scores.

**Access:** authentication was omitted due to the time constraint. The public
endpoint can trigger billable model calls; authentication and per-client
quotas would be priorities before wider use.

**Verification:** 46 offline tests pass. All 13 deployed regression cases
matched expected tiers/routing, taking 2.26–4.47 seconds per request.
[Cases](test/fixtures/leads.json) and [results](test/eval/deployed-results.json)
are reviewable; this small set was used during calibration.

Configure `.env` from `.env.example`, then:

```powershell
poetry install
poetry run uvicorn app:app --reload
poetry run pytest
```

**With more time, I would focus on:**

- **Model benchmarks:** compare models on the same held-out conversations,
  measuring scoring quality, repeated-run consistency, latency, and cost.
- **Scoring methods:** compare the current contextual scoring with revised
  rubric weights and LLM extraction followed by deterministic scoring. Check
  whether the weights and tier thresholds reflect actual sales priorities.
- **Deeper evaluation:** expand the cases with borderline, incomplete, and
  contradictory conversations. Review expected labels and LLM-judge decisions
  with a human, inspect failures, and reserve cases unused during prompt
  development so improvements are tested on new examples.
- **Observability:** add request IDs and structured metrics for latency, token
  usage, cost, errors, and score distributions. Record model and prompt versions
  to trace regressions while keeping API keys and raw conversations out of logs.

[Deployment instructions](DEPLOY.md) · [Decision history](DECISIONS.md)
