"""One structured OpenAI call under a total elapsed-time deadline."""

import asyncio
from typing import Protocol

from openai import APITimeoutError, AsyncOpenAI, OpenAIError, RateLimitError
from pydantic import ValidationError

from config import Settings
from llm.prompt import SYSTEM_PROMPT
from schemas import LeadAssessment, LeadRequest


class ScoringError(Exception):
    def __init__(self, code: str, status_code: int, message: str):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.message = message


class LeadScorer(Protocol):
    async def score(self, lead: LeadRequest) -> LeadAssessment: ...


def create_client(settings: Settings) -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=settings.llm_deadline_seconds,
        max_retries=0,
    )


class OpenAILeadScorer:
    def __init__(self, client: AsyncOpenAI, settings: Settings):
        self.client = client
        self.settings = settings

    async def score(self, lead: LeadRequest) -> LeadAssessment:
        try:
            async with asyncio.timeout(self.settings.llm_deadline_seconds):
                response = await self.client.responses.parse(
                    model=self.settings.openai_model,
                    instructions=SYSTEM_PROMPT,
                    input=[
                        {
                            "role": "user",
                            "content": lead.model_dump_json(exclude={"lead_id"}),
                        }
                    ],
                    text_format=LeadAssessment,
                    reasoning={"effort": self.settings.llm_reasoning_effort},
                    max_output_tokens=1024,
                    store=False,
                )
                if any(
                    part.type == "refusal"
                    for item in response.output
                    if item.type == "message"
                    for part in item.content
                ):
                    raise ScoringError(
                        "model_refusal", 502, "The model declined to assess this conversation."
                    )
                if response.status != "completed":
                    raise ScoringError(
                        "model_incomplete", 502, "The model did not complete the assessment."
                    )
                if response.output_parsed is None:
                    raise ScoringError(
                        "invalid_assessment", 502, "The model returned no valid assessment."
                    )
                return LeadAssessment.model_validate(response.output_parsed)
        except (TimeoutError, APITimeoutError):
            raise ScoringError(
                "scoring_timeout", 504, "The assessment exceeded its configured deadline."
            ) from None
        except RateLimitError:
            raise ScoringError(
                "upstream_unavailable", 503, "The model provider is temporarily unavailable."
            ) from None
        except ValidationError:
            raise ScoringError(
                "invalid_assessment", 502, "The model returned an invalid assessment."
            ) from None
        except OpenAIError:
            raise ScoringError(
                "upstream_failure", 502, "The model provider could not complete the assessment."
            ) from None
