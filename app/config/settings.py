from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    shopify_store_domain: str
    shopify_access_token: str
    shopify_storefront_token: str
    shopify_api_version: str = "2026-07"

    llm_provider: str = "ollama"
    llm_model: str = "gpt-oss:20b"
    google_api_key: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_version: str | None = None
    azure_openai_deployment: str | None = None

    database_url: str
    langgraph_checkpoint_database_url: str

    # Phase 5A security. dev_header is ONLY for local POC use.
    auth_mode: str = "dev_header"
    dev_user_id: str | None = None
    dev_shopify_customer_id: str | None = None
    dev_user_roles: str = "customer"

    # Business/security guardrail. Keep this at or below the quantity
    # behavior supported by the current storefront implementation.
    max_cart_item_quantity: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()