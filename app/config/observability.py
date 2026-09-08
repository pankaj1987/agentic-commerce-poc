import os
import logging

logger = logging.getLogger(__name__)


def validate_langsmith():
    tracing = os.getenv("LANGSMITH_TRACING")
    project = os.getenv("LANGSMITH_PROJECT")
    api_key = os.getenv("LANGSMITH_API_KEY")

    logger.info(
        "LangSmith configuration: tracing=%s project=%s api_key_present=%s",
        tracing,
        project,
        bool(api_key),
    )