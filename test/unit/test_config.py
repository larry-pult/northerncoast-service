import pytest
from pydantic import ValidationError

from config import Settings


@pytest.mark.parametrize("deadline", [0, -1, 26, float("inf"), float("nan")])
def test_deadline_reserves_http_headroom(deadline):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, openai_api_key="test-key", llm_deadline_seconds=deadline)


def test_environment_selects_model_and_deadline(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "different-model")
    monkeypatch.setenv("LLM_DEADLINE_SECONDS", "20")
    settings = Settings(_env_file=None)
    assert settings.openai_model == "different-model"
    assert settings.llm_deadline_seconds == 20


def test_configuration_errors_do_not_display_the_key():
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, openai_api_key="private-test-value", llm_deadline_seconds=30)
    assert "private-test-value" not in str(error.value)
