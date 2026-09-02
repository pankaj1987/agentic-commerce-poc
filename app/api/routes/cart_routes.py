from fastapi import APIRouter, HTTPException, Query, status

from app.api.schemas.cart_schemas import (
    AddCartItemRequest,
    UpdateCartItemRequest,
    RemoveCartItemRequest,
    PromotionRequest,
)

from app.services.cart_service import CartService


router = APIRouter()


# ============================================================
# CREATE CART
# POST /api/cart
# ============================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_cart():
    """
    Create a new Shopify cart.
    """

    try:
        result = CartService.create_cart()

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=result.get(
                    "message",
                    "Unable to create cart.",
                ),
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to create cart: {str(exc)}",
        ) from exc


# ============================================================
# GET CART
# GET /api/cart?cart_id=<SHOPIFY_CART_ID>
# ============================================================

@router.get("")
def get_cart(
    cart_id: str = Query(
        ...,
        min_length=1,
        description=(
            "Complete Shopify cart ID, including the "
            "?key=... component returned by Shopify."
        ),
    ),
):
    """
    Retrieve the current Shopify cart.

    Example Shopify cart ID:

    gid://shopify/Cart/ABC123?key=XYZ456

    The ID is passed as a query parameter rather than a URL
    path parameter because Shopify cart IDs contain reserved
    URL characters.
    """

    try:
        result = CartService.get_cart(
            cart_id=cart_id,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get(
                    "message",
                    "Cart not found.",
                ),
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to retrieve cart: {str(exc)}",
        ) from exc


# ============================================================
# ADD ITEM
# POST /api/cart/items
# ============================================================

@router.post("/items")
def add_cart_item(
    request: AddCartItemRequest,
):
    """
    Add an already-resolved Shopify product variant
    to the customer's cart.
    """

    try:
        result = CartService.add_to_cart(
            cart_id=request.cart_id,
            variant_id=request.variant_id,
            quantity=request.quantity,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get(
                    "message",
                    "Unable to add item to cart.",
                ),
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to add item to cart: {str(exc)}",
        ) from exc


# ============================================================
# UPDATE ITEM QUANTITY
# PATCH /api/cart/items
# ============================================================

@router.patch("/items")
def update_cart_item(
    request: UpdateCartItemRequest,
):
    """
    Update the quantity of an existing Shopify cart line.
    """

    try:
        result = CartService.update_item(
            cart_id=request.cart_id,
            line_id=request.line_id,
            quantity=request.quantity,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get(
                    "message",
                    "Unable to update cart item.",
                ),
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to update cart item: {str(exc)}",
        ) from exc


# ============================================================
# REMOVE ITEM
# POST /api/cart/items/remove
# ============================================================

@router.post("/items/remove")
def remove_cart_item(
    request: RemoveCartItemRequest,
):
    """
    Remove an existing Shopify cart line.

    POST is intentionally used instead of putting the Shopify
    line ID in the URL because Shopify IDs contain reserved
    URL characters.
    """

    try:
        result = CartService.remove_item(
            cart_id=request.cart_id,
            line_id=request.line_id,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get(
                    "message",
                    "Unable to remove cart item.",
                ),
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to remove cart item: {str(exc)}",
        ) from exc


# ============================================================
# APPLY PROMOTION
# POST /api/cart/promotion
# ============================================================

@router.post("/promotion")
def apply_cart_promotion(
    request: PromotionRequest,
):
    """
    Apply a Shopify promotion/discount code to the cart.

    Shopify remains the source of truth for whether the
    promotion is actually applicable.
    """

    try:
        result = CartService.apply_discount(
            cart_id=request.cart_id,
            discount_code=request.discount_code,
        )

        # A promotion being not-applicable is a valid commerce
        # outcome, not necessarily an API/system failure.
        #
        # Therefore return the structured result to the UI.
        if result.get("status") in {
            "not_applicable",
            "not_applied",
            "rejected",
        }:
            return result

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get(
                    "message",
                    "Unable to apply promotion.",
                ),
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to apply promotion: {str(exc)}",
        ) from exc