import os

from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.settings import settings


def get_llm():
    provider = settings.llm_provider.lower()
    print(f"LLM Provider: {provider}, Model: {settings.llm_model}")
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

    if provider == "openai":
        print("Azure endpoint:", settings.azure_openai_endpoint)
        print("Azure deployment:", settings.azure_openai_deployment)
        print("Azure API version:", settings.azure_openai_api_version)
        print(
            "API key loaded:",
            bool(settings.azure_openai_api_key)
        )
        return AzureChatOpenAI(
            temperature=0,
            azure_deployment=settings.azure_openai_deployment,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
        )

    raise ValueError(
        f"Unsupported LLM provider: {settings.llm_provider}"
    )