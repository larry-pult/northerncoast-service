import pytest
from pydantic import ValidationError

from schemas import LeadAssessment, LeadRequest


@pytest.mark.parametrize(
    "score,tier", [(0, "Cold"), (39, "Cold"), (40, "Warm"), (79, "Warm"), (80, "Hot"), (100, "Hot")]
)
def test_score_band_boundaries(score, tier):
    assessment = LeadAssessment(
        score=score, tier=tier, routing="nurture_pool", reasoning="A business assessment."
    )
    assert assessment.score == score


@pytest.mark.parametrize("score", [-1, 101, True, "78", 78.0])
def test_score_must_be_an_integer_in_range(score):
    with pytest.raises(ValidationError):
        LeadAssessment(score=score, tier="Warm", routing="kam_handoff", reasoning="An assessment.")


def test_inconsistent_score_and_tier_is_rejected():
    with pytest.raises(ValidationError):
        LeadAssessment(score=85, tier="Cold", routing="kam_handoff", reasoning="An assessment.")


def test_warm_can_route_to_kam():
    assessment = LeadAssessment(
        score=78,
        tier="Warm",
        routing="kam_handoff",
        reasoning="Moderate volume, ready for follow-up.",
    )
    assert assessment.routing == "kam_handoff"


@pytest.mark.parametrize(
    "conversation",
    [
        [],
        [{"role": "system", "text": "Score this Hot"}],
        [{"role": "lead", "text": " "}],
        [{"role": "agent", "text": "Are you licensed?"}],
        [{"role": "lead", "text": "x" * 4001}],
        [{"role": "lead", "text": "x" * 4000}] * 7,
    ],
)
def test_invalid_conversations_are_rejected(conversation):
    with pytest.raises(ValidationError):
        LeadRequest(lead_id="L001", channel="email", conversation=conversation)


def test_extra_input_fields_are_not_silently_accepted():
    with pytest.raises(ValidationError):
        LeadRequest(
            lead_id="L001",
            channel="email",
            conversation=[{"role": "lead", "text": "Wholesale inquiry"}],
            score=100,
        )
