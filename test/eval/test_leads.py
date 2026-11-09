import asyncio
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from api.application import create_app
from config import Settings
from llm.client import create_client
from llm.prompt import SYSTEM_PROMPT
from schemas import LeadRequest, LeadResponse
from test.eval.judge import judge_rationale

pytestmark = pytest.mark.llm_eval
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
CASES = [
    {**case, "source": name}
    for name in ("leads.json", "brief_examples.json")
    for case in json.loads((FIXTURES / name).read_text(encoding="utf-8"))["cases"]
]


@pytest.fixture(scope="session")
def live_settings():
    return Settings()


@pytest.fixture(scope="session")
def send_lead(pytestconfig, live_settings):
    endpoint = pytestconfig.getoption("--endpoint")
    if endpoint:
        with httpx.Client(timeout=30) as client:
            yield lambda payload: client.post(endpoint, json=payload)
    else:
        with TestClient(create_app(settings=live_settings)) as client:
            yield lambda payload: client.post("/api/score", json=payload)


@pytest.fixture(scope="session")
def evaluation_report(pytestconfig, live_settings):
    results = []
    yield results
    report = Path(pytestconfig.getoption("--eval-report"))
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model": live_settings.openai_model,
                "prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
                "deadline_seconds": live_settings.llm_deadline_seconds,
                "endpoint": pytestconfig.getoption("--endpoint") or "local ASGI app",
                "judge_model": (
                    pytestconfig.getoption("--judge-model") or live_settings.openai_model
                )
                if pytestconfig.getoption("--judge")
                else None,
                "label_status": "Proposed expectations; model agreement does not establish business accuracy.",
                "results": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_live_lead(case, send_lead, live_settings, evaluation_report, pytestconfig):
    lead = LeadRequest.model_validate(case["input"])
    started = time.perf_counter()
    response = send_lead(lead.model_dump())
    elapsed = time.perf_counter() - started
    record = {
        "id": case["id"],
        "source": case["source"],
        "expected": case["expected"],
        "elapsed_seconds": round(elapsed, 3),
        "status_code": response.status_code,
        "actual": response.json(),
    }
    evaluation_report.append(record)
    assert response.status_code == 200, record
    result = LeadResponse.model_validate(response.json())
    record["tier_matches"] = result.tier == case["expected"]["tier"]
    record["routing_matches"] = result.routing in case["expected"]["acceptable_routes"]

    if pytestconfig.getoption("--judge"):

        async def review():
            async with create_client(live_settings) as client:
                return await judge_rationale(
                    client,
                    pytestconfig.getoption("--judge-model") or live_settings.openai_model,
                    lead,
                    result,
                    case["expected"]["reasoning_checks"],
                    live_settings.llm_deadline_seconds,
                )

        try:
            judgment = asyncio.run(review())
            record["judge"] = judgment.model_dump()
        except Exception as error:
            record["judge_error"] = type(error).__name__
            pytest.fail(f"Judge failed: {type(error).__name__}; see the evaluation report")
        assert judgment.grounded and judgment.coherent, record

    assert elapsed < 30, record
    assert elapsed < live_settings.llm_deadline_seconds + 1, record
    assert result.lead_id == lead.lead_id, record
    assert record["tier_matches"], record
    assert record["routing_matches"], record
