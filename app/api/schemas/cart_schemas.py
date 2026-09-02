from typing import Any

from pydantic import BaseModel, Field


# ============================================================
# CREATE CART
# ============================================================

class CreateCartResponse(BaseModel):
    success: bool
    cart: dict[str, Any]


# ============================================================
# GET CART
# ============================================================

class GetCartResponse(BaseModel):
    success: bool
    cart: dict[str, Any]


# ============================================================
# ADD CART ITEM
# ============================================================

class AddCartItemRequest(BaseModel):
    cart_id: str = Field(
        ...,
        description=(
            "Complete Shopify cart ID including the ?key= value"
        ),
    )

    variant_id: str = Field(
        ...,
        description="Shopify product variant ID",
    )

    quantity: int = Field(
        default=1,
        gt=0,
        description="Quantity to add",
    )


# ============================================================
# UPDATE CART ITEM
# ============================================================

class UpdateCartItemRequest(BaseModel):
    cart_id: str = Field(
        ...,
        description=(
            "Complete Shopify cart ID including the ?key= value"
        ),
    )

    line_id: str = Field(
        ...,
        description="Shopify cart line ID",
    )

    quantity: int = Field(
        ...,
        gt=0,
        description="New quantity",
    )


# ============================================================
# REMOVE CART ITEM
# ============================================================

class RemoveCartItemRequest(BaseModel):
    cart_id: str = Field(
        ...,
        description=(
            "Complete Shopify cart ID including the ?key= value"
        ),
    )

    line_id: str = Field(
        ...,
        description="Shopify cart line ID",
    )


# ============================================================
# PROMOTION
# ============================================================

class PromotionRequest(BaseModel):
    cart_id: str = Field(
        ...,
        description=(
            "Complete Shopify cart ID including the ?key= value"
        ),
    )

    discount_code: str = Field(
        ...,
        min_length=1,
        description="Shopify discount code",
    )