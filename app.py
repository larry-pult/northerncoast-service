"""Uvicorn and Vercel both serve this ASGI application."""

from api.application import create_app

app = create_app()
