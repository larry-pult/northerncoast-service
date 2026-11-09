# Northern Coast lead scoring

[Live POST endpoint](https://northerncoast-service.vercel.app/api/score) ·
[API explorer](https://northerncoast-service.vercel.app/docs) ·
[Source](https://github.com/larry-pult/northerncoast-service)

**Time spent: 82 minutes (1 hour 22 minutes).**

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

With more time: human-labeled held-out evaluation, repeated-run stability,
deterministic-scoring comparison, authentication, quotas, and monitoring.

[Deployment instructions](DEPLOY.md) · [Decision history](DECISIONS.md)
