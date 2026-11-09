# Northern Coast lead scoring

`POST /api/score` accepts the brief's transcript and returns `lead_id`, `score`,
`tier`, `routing`, and a short rationale. FastAPI/Pydantic validate both
boundaries; one OpenAI Responses call produces the assessment using Structured
Outputs. The application preserves the original lead ID.

Default model: **`gpt-6-luna`**, chosen for a bounded, cost-sensitive classification
task. Model, reasoning effort, and deadline are configurable in `.env`; see
[`.env.example`](.env.example). The default elapsed-time deadline is ten seconds,
with no retries. Invalid requests receive 422; unusable/provider responses 502;
provider throttling 503; deadline expiration 504.

The rubric allocates 35 points to volume, 25 to credibility, 20 to product fit,
and 20 to readiness. Volume leads because this is container-load wholesale.
Hot starts at 80, Warm at 40. Licensing remains self-reported evidence. Routing
selects the next action, allowing actionable Warm leads to reach a KAM.

```powershell
poetry install
poetry run uvicorn app:app --reload
poetry run pytest
```

Validation: 46 offline tests and 13 live cases passed; final scoring requests
took 1.77–4.25 seconds locally. [Cases](test/fixtures/leads.json),
[results](test/eval/results.json), and [evaluation notes](DECISIONS.md) are reviewable.

With more time: evaluate human-labeled, held-out leads and repeated-run stability;
compare deterministic signal scoring; add authentication, quotas, and monitoring.
See [DEPLOY.md](DEPLOY.md) for setup, evaluation commands, and manual Vercel deployment.
