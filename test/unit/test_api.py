from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from api.application import create_app
from llm.client import ScoringError
from schemas import LeadAssessment


@pytest.fixture
def scorer():
    return SimpleNamespace(
        score=AsyncMock(
            return_value=LeadAssessment(
                score=78,
                tier="Warm",
                routing="kam_handoff",
                reasoning="An actionable moderate-volume wholesale inquiry.",
            )
        )
    )


@pytest.fixture
def payload():
    return {
        "lead_id": "original-id",
        "channel": "email",
        "conversation": [{"role": "lead", "text": "We need 1 FCL/month of Monster Energy."}],
    }


def test_post_preserves_id_and_returns_exact_contract(scorer, payload):
    with TestClient(create_app(scorer=scorer)) as client:
        response = client.post("/api/score", json=payload)
    assert response.status_code == 200
    assert response.json() == {
        "lead_id": "original-id",
        "score": 78,
        "tier": "Warm",
        "routing": "kam_handoff",
        "reasoning": "An actionable moderate-volume wholesale inquiry.",
    }
    scorer.score.assert_awaited_once()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"lead_id": 123, "channel": "email", "conversation": []},
        {"lead_id": "L", "channel": "email", "conversation": [{"role": "lead", "text": ""}]},
    ],
)
def test_invalid_input_never_calls_model(scorer, payload):
    with TestClient(create_app(scorer=scorer)) as client:
        response = client.post("/api/score", json=payload)
    assert response.status_code == 422
    scorer.score.assert_not_awaited()


def test_malformed_json_never_calls_model(scorer):
    with TestClient(create_app(scorer=scorer)) as client:
        response = client.post(
            "/api/score", content="{", headers={"Content-Type": "application/json"}
        )
    assert response.status_code == 422
    scorer.score.assert_not_awaited()


@pytest.mark.parametrize(
    "status,code",
    [(502, "upstream_failure"), (503, "upstream_unavailable"), (504, "scoring_timeout")],
)
def test_failed_assessments_return_errors_without_a_score(scorer, payload, status, code):
    scorer.score.side_effect = ScoringError(code, status, "Assessment failed.")
    with TestClient(create_app(scorer=scorer)) as client:
        response = client.post("/api/score", json=payload)
    assert response.status_code == status
    assert response.json() == {"error": {"code": code, "message": "Assessment failed."}}
    assert "score" not in response.json()
