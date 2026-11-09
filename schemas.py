"""HTTP contracts and the structured assessment returned by OpenAI."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints, model_validator

Tier = Literal["Hot", "Warm", "Cold"]
Routing = Literal["kam_handoff", "nurture_pool", "auto_archive"]
Text = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]
LeadID = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=128)]


class ConversationMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["lead", "agent"]
    text: Annotated[Text, Field(max_length=4000)]


class LeadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lead_id: LeadID
    channel: Annotated[Text, Field(max_length=64)]
    conversation: list[ConversationMessage] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_content(self) -> Self:
        if not self.lead_id.strip():
            raise ValueError("lead_id must not be blank")
        if not any(message.role == "lead" for message in self.conversation):
            raise ValueError("conversation must contain a lead message")
        if sum(len(message.text) for message in self.conversation) > 24000:
            raise ValueError("conversation must contain at most 24000 text characters")
        return self


class LeadAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: Annotated[StrictInt, Field(ge=0, le=100)]
    tier: Tier
    routing: Routing
    reasoning: Annotated[Text, Field(max_length=600)]

    @model_validator(mode="after")
    def require_consistent_tier(self) -> Self:
        expected = "Hot" if self.score >= 80 else "Warm" if self.score >= 40 else "Cold"
        if self.tier != expected:
            raise ValueError("tier does not match the rubric's score band")
        return self


class LeadResponse(LeadAssessment):
    lead_id: LeadID
