# Deploy and verify

**Scoring:** POST <https://northerncoast-service.vercel.app/api/score>

**Try it:** <https://northerncoast-service.vercel.app/docs>

Public verification on 2026-11-09 passed all 13 evaluation cases. Scoring took
2.26–4.47 seconds, including network time; missing fields and malformed JSON
returned 422. No authentication was supplied. These checks followed a health
request, so cold-start latency was not isolated.
[Full results](test/eval/deployed-results.json).

## Reproduce the deployment

1. Import [the GitHub repository](https://github.com/larry-pult/northerncoast-service)
   into Vercel. Use repository root `.` and the **FastAPI** preset with
   **Python 3.12**. `app.py` exports the application; keep build/output defaults.
2. Set these Vercel environment variables, then deploy:

   ```dotenv
   OPENAI_API_KEY=your-secret-key
   OPENAI_MODEL=gpt-6-luna
   LLM_DEADLINE_SECONDS=10
   LLM_REASONING_EFFORT=none
   ```

3. Allow public access to the submitted production endpoint. A reviewer must
   be able to POST without signing into Vercel.

`vercel.json` sets a 30-second function limit. The model deadline is configurable
up to 25 seconds; reasoning effort must suit the selected model. Redeploy after
changing environment settings. Secrets, tests, and local caches are excluded.

Poetry manages dependencies; `requirements.txt` contains runtime pins from
`poetry.lock`. Refresh that export when dependencies change. Vercel's
[FastAPI](https://vercel.com/docs/frameworks/backend/fastapi) and
[Python runtime](https://vercel.com/docs/functions/runtimes/python) docs describe
the supported entrypoint and dependency files.

## Run checks

Run from `test-1-build/submission/`. For local setup, use a fresh terminal,
Python 3.12, Poetry 2.1+, and `.env` configured from `.env.example`:

```powershell
$env:POETRY_VIRTUALENVS_IN_PROJECT = "true"
poetry install
poetry run pytest
```

Offline tests need no API key. With local `.env` configured, these opt-in
commands make paid calls:

```powershell
poetry run pytest test/eval --run-llm --judge
poetry run pytest test/eval --run-llm --endpoint https://northerncoast-service.vercel.app/api/score
```

The first checks the local app and adds a rationale judge. The second checks
Vercel; match local model/deadline settings to the deployment. Reports go to
`.cache/eval-results.json`. Recheck the public endpoint after changes.

For the final submission ZIP, use clean tracked files and omit `.env`, `.venv`,
and caches. The 82-minute time report is recorded in [README.md](README.md).
