from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.settings import settings


def get_llm():
    provider = settings.llm_provider.lower()

    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=0,
            google_api_key=settings.google_api_key,
        )

    if provider == "ollama":
        return ChatOllama(
            model=settings.llm_model,
            temperature=0,
        )

    raise ValueError(
        f"Unsupported LLM provider: {settings.llm_provider}"
    )