"""Environment configuration; importing the app does not read credentials."""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, StringConstraints, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=APP_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    openai_api_key: SecretStr
    openai_model: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = (
        "gpt-6-luna"
    )
    llm_deadline_seconds: float = Field(default=10, gt=0, le=25, allow_inf_nan=False)
    llm_reasoning_effort: Literal["none", "low", "medium", "high", "xhigh", "max"] = "none"

    @field_validator("openai_api_key")
    @classmethod
    def require_key(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("OPENAI_API_KEY must be configured")
        return value
