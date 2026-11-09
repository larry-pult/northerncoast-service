from typing import Annotated

from fastapi import APIRouter, Depends, Request

from llm.client import LeadScorer
from schemas import LeadRequest, LeadResponse

router = APIRouter()


def get_scorer(request: Request) -> LeadScorer:
    return request.app.state.scorer


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/score", response_model=LeadResponse)
async def score_lead(
    lead: LeadRequest,
    scorer: Annotated[LeadScorer, Depends(get_scorer)],
) -> LeadResponse:
    assessment = await scorer.score(lead)
    return LeadResponse(lead_id=lead.lead_id, **assessment.model_dump())
