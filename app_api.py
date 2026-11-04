"""Deployment entry point (Hugging Face Spaces): uvicorn app_api:app --host 0.0.0.0 --port 7860"""
from src.api.main import app  # noqa: F401
