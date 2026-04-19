"""Vertex AI and Gemini client initialization."""

from __future__ import annotations

import os

from google import genai
import google.cloud.aiplatform as aiplatform

from app.config import Config
from app.services.logging_client import logger
from app.services.secrets import get_secret


def _init_vertex_ai() -> None:
    """Explicitly initialize Vertex AI platform."""
    if Config.PROJECT:
        try:
            aiplatform.init(project=Config.PROJECT, location=Config.REGION)
            logger.info("Vertex AI initialized: %s/%s", Config.PROJECT, Config.REGION)
        except Exception as exc:
            logger.warning("Vertex AI init: %s", exc)


def _init_gemini() -> genai.Client | None:
    """Initialize Gemini — API key preferred locally, Vertex AI in cloud."""
    _init_vertex_ai()
    
    # Try API key first if provided (standard for local dev)
    api_key = os.environ.get("GEMINI_API_KEY", "") or get_secret("gemini-api-key")
    
    # In cloud (Cloud Run), prefer Vertex AI if PROJECT is set
    if Config.IS_CLOUD and Config.PROJECT:
        logger.info("Gemini: Vertex AI project %s (Cloud Mode)", Config.PROJECT)
        return genai.Client(vertexai=True, project=Config.PROJECT, location=Config.REGION)
    
    # Otherwise, use API key if available
    if api_key:
        logger.info("Gemini: API key mode")
        return genai.Client(api_key=api_key)
        
    # Fallback to Vertex AI locally if project set but no key
    if Config.PROJECT:
        try:
            logger.info("Gemini: Vertex AI project %s (Local Fallback)", Config.PROJECT)
            return genai.Client(vertexai=True, project=Config.PROJECT, location=Config.REGION)
        except Exception as exc:
            logger.warning("Gemini: Vertex AI local init failed: %s", exc)

    logger.warning("Gemini: No API key or Project ID found. Application may have limited functionality.")
    return None


gemini_client = _init_gemini()
