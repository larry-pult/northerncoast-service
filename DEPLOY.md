# Setup and manual deployment

The service root is `test-1-build/submission/`. Git is initialized here with
`origin` set to <https://github.com/larry-pult/northerncoast-service>.

## Local setup

Use Python 3.12 and Poetry 2.1 or later. From this directory in a fresh PowerShell
terminal, create the environment and install the locked application and test dependencies:

```powershell
$env:POETRY_VIRTUALENVS_IN_PROJECT = "true"
poetry install
```

The existing local `.env` already contains the working credential. For a fresh
checkout, copy `.env.example` to `.env` and set `OPENAI_API_KEY`. Environment
variables take precedence over `.env`. Never commit the actual credential.

| Setting | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | Required | Provider credential |
| `OPENAI_MODEL` | `gpt-6-luna` | Model with Responses API and Structured Outputs support |
| `LLM_DEADLINE_SECONDS` | `10` | Total elapsed model-operation budget; greater than 0 and at most 25 |
| `LLM_REASONING_EFFORT` | `none` | Must be supported by the chosen model; use an appropriate value when changing models |

The 25-second configuration ceiling reserves headroom under the brief's
30-second response requirement. The SDK has retries explicitly disabled.

```powershell
poetry run uvicorn app:app --reload
```

API documentation: <http://127.0.0.1:8000/docs>. Liveness: `/health`.
The health route does not call OpenAI or verify provider availability.

Send an actual fixture input, excluding its expected label:

```powershell
$cases = Get-Content test/fixtures/leads.json -Raw | ConvertFrom-Json
$body = $cases.cases[0].input | ConvertTo-Json -Depth 10
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/score -ContentType application/json -Body $body
```

## Verification

Run these commands from the service root:

```powershell
poetry run pytest
poetry run ruff check .
poetry run ruff format --check .
```

Default tests are offline: live tests are skipped and no credential is required.
These explicit commands make paid API calls:

```powershell
poetry run pytest test/eval --run-llm
poetry run pytest test/eval --run-llm --judge
```

The second command adds one judge call per successful assessment, outside the
scorer's measured latency. `--judge-model MODEL_ID` selects a different judge;
the default is `OPENAI_MODEL`. Judge agreement remains advisory evidence about
quality, not ground truth. Assertions fail if the judge flags an issue.

Reports default to ignored `.cache/eval-results.json`; choose a different path
with `--eval-report PATH`. The committed `test/eval/results.json` records the
final verification run, including the scorer prompt hash. There are nine
synthetic cases and four examples from the brief, including its output example.

Requests require a nonblank lead ID (at most 128 characters), a nonblank channel
(at most 64), and 1–100 messages with `lead`/`agent` roles. Each message permits
at most 4,000 text characters; total text is capped at 24,000 characters. At
least one lead message is required. Invalid inputs receive 422, without a model
call. Unspecified channel names are accepted. Provider error details are not
returned to clients, and the application does not log transcripts or credentials.

## GitHub and Vercel

The candidate performs these external steps manually:

1. Review the local commits, then push `main` to the configured GitHub remote.
2. Import `larry-pult/northerncoast-service` in Vercel. Because the repository
   itself is the service, use `.` as the project root. Select the FastAPI preset.
3. Use Python 3.12. `app.py` exports the ASGI application. Leave build/output
   settings at the framework defaults. Runtime dependencies are declared in
   `pyproject.toml`; `requirements.txt` contains runtime-only pins from
   `poetry.lock`. Updating dependencies also requires refreshing those pins
   using Poetry's export plugin.
4. Set `OPENAI_API_KEY`, `OPENAI_MODEL`, `LLM_DEADLINE_SECONDS`, and
   `LLM_REASONING_EFFORT` in Vercel for the deployment environment. The local
   `.env` is excluded. Redeploy after changing environment settings.
5. Deploy and record the production URL. `vercel.json` sets the function limit
   to 30 seconds and excludes tests, caches, and local environment files.
6. Verify that the production endpoint accepts a POST without a Vercel login.
   Deployment Protection must permit the evaluator's public requests.

Vercel documents the [FastAPI entrypoint and function settings](https://vercel.com/docs/frameworks/backend/fastapi)
and [Python dependency files](https://vercel.com/docs/functions/runtimes/python).
Local verification does not establish Vercel cold-start behavior; verify the
deployed URL before submitting.

Match local model/deadline settings to the deployment, then run:

```powershell
poetry run pytest test/eval --run-llm --endpoint https://YOUR-PROJECT.vercel.app/api/score --eval-report .cache/deployed-results.json
```

Before sending the take-home, supply the actual endpoint URL and honest hours
spent. No live Vercel URL or time-spent estimate is invented in this repository.

For the final take-home ZIP, export the tracked service files and place them in
the clean assessment's `test-1-build/submission/` directory. Avoid archiving this
working directory directly: Git ignore rules do not exclude `.env`, `.venv`, or
caches from an ordinary ZIP operation.
