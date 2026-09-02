from pydantic import BaseModel, Field


class ChatRequest(BaseModel):

    message: str = Field(
        ...,
        min_length=1,
        description="Customer message",
    )

    cart_id: str | None = None


class ChatResponse(BaseModel):

    success: bool

    response: str

    cart_id: str | None = None