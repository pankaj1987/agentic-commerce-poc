from typing import Any

from pydantic import BaseModel, Field


class CartResponse(BaseModel):
    """Public cart response.

    Shopify cart_id is deliberately not exposed as a top-level API field.
    The Shopify cart payload may contain its own id internally; the frontend
    must not persist or send that value back to the API.
    """

    success: bool
    session_id: str
    cart: dict[str, Any] | None = None
    message: str | None = None
    status: str | None = None


class SessionCartRequest(BaseModel):
    session_id: str | None = Field(
        default=None,
        max_length=128,
        description="Public commerce session ID.",
    )


class AddCartItemRequest(BaseModel):
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Public commerce session ID.",
    )
    variant_id: str = Field(
        ...,
        min_length=1,
        description="Shopify product variant ID.",
    )
    quantity: int = Field(
        default=1,
        gt=0,
        description="Quantity to add.",
    )


class UpdateCartItemRequest(BaseModel):
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )
    line_id: str = Field(
        ...,
        min_length=1,
        description="Shopify cart line ID.",
    )
    quantity: int = Field(
        ...,
        gt=0,
        description="New quantity.",
    )


class RemoveCartItemRequest(BaseModel):
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )
    line_id: str = Field(
        ...,
        min_length=1,
        description="Shopify cart line ID.",
    )


class PromotionRequest(BaseModel):
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )
    discount_code: str = Field(
        ...,
        min_length=1,
        description="Shopify discount code.",
    )
