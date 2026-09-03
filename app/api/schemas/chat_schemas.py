# app/api/schemas/chat_schemas.py

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Request sent by the browser.

    The browser owns only the public commerce session ID.

    It must NOT send:
    - Shopify cart_id
    - LangGraph thread_id
    """

    message: str = Field(
        min_length=1,
        max_length=10000,
    )

    # None for the first request.
    #
    # The backend creates the session and returns session_id.
    # The browser sends that session_id on later requests.
    session_id: str | None = Field(
        default=None,
        max_length=128,
    )


class ChatResponse(BaseModel):
    """
    Public chat response.

    Shopify cart_id and LangGraph thread_id are intentionally
    not exposed to the browser.
    """

    success: bool

    response: str

    session_id: str

    cart_changed: bool = False