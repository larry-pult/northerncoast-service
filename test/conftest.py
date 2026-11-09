import pytest


def pytest_addoption(parser):
    group = parser.getgroup("model evaluation")
    group.addoption("--run-llm", action="store_true", help="Enable paid live model evaluations")
    group.addoption("--judge", action="store_true", help="Also use an LLM to review each rationale")
    group.addoption("--judge-model", default=None, help="Judge model; defaults to OPENAI_MODEL")
    group.addoption(
        "--endpoint", default=None, help="Score an external /api/score URL instead of the local app"
    )
    group.addoption(
        "--eval-report", default=".cache/eval-results.json", help="JSON path for model results"
    )


def pytest_configure(config):
    if config.getoption("--judge") and not config.getoption("--run-llm"):
        raise pytest.UsageError("--judge requires --run-llm")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-llm"):
        skip = pytest.mark.skip(reason="Use --run-llm to enable paid model calls")
        for item in items:
            if "llm_eval" in item.keywords:
                item.add_marker(skip)
