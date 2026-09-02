from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    shopify_store_domain: str
    shopify_access_token: str
    shopify_storefront_token: str
    shopify_api_version: str = "2026-07"

    llm_provider: str = "ollama"
    llm_model: str = "gpt-oss:20b"
    google_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()