import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.routes import router
from config import Settings
from llm.client import LeadScorer, OpenAILeadScorer, ScoringError, create_client

logger = logging.getLogger(__name__)


def create_app(scorer: LeadScorer | None = None, settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if scorer is not None:
            app.state.scorer = scorer
            yield
        else:
            configured = settings if settings is not None else Settings()
            async with create_client(configured) as client:
                app.state.scorer = OpenAILeadScorer(client, configured)
                yield

    app = FastAPI(title="Northern Coast Lead Scoring", version="0.1.0", lifespan=lifespan)
    app.include_router(router)

    @app.exception_handler(ScoringError)
    async def scoring_error(request: Request, error: ScoringError) -> JSONResponse:
        logger.warning("Lead assessment failed: %s", error.code)
        return JSONResponse(
            status_code=error.status_code,
            content={"error": {"code": error.code, "message": error.message}},
        )

    return app
