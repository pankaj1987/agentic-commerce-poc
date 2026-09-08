from fastapi import APIRouter, HTTPException, Query, status

from app.api.schemas.cart_schemas import (
    AddCartItemRequest,
    PromotionRequest,
    RemoveCartItemRequest,
    SessionCartRequest,
    UpdateCartItemRequest,
)
from app.services.session_cart_service import SessionCartService


router = APIRouter()


def _raise_for_failure(result: dict, default_message: str) -> None:
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", default_message),
        )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_or_restore_cart(
    request: SessionCartRequest | None = None,
):
    """Create/reuse the cart associated with a public session.

    With session_id=None a new CommerceSession and Shopify cart are created.
    With an existing session_id the same cart is restored when still valid.
    """

    try:
        session_id = request.session_id if request else None
        result = SessionCartService.initialize_cart(session_id)
        _raise_for_failure(result, "Unable to initialize cart.")
        return result
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to initialize cart: {str(exc)}",
        ) from exc


@router.get("")
def get_cart(
    session_id: str = Query(..., min_length=1, max_length=128),
):
    try:
        result = SessionCartService.get_cart(session_id)
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "Cart not found."),
            )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to retrieve cart: {str(exc)}",
        ) from exc


@router.post("/items")
def add_cart_item(request: AddCartItemRequest):
    try:
        result = SessionCartService.add_item(
            session_id=request.session_id,
            variant_id=request.variant_id,
            quantity=request.quantity,
        )
        _raise_for_failure(result, "Unable to add item to cart.")
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to add item to cart: {str(exc)}",
        ) from exc


@router.patch("/items")
def update_cart_item(request: UpdateCartItemRequest):
    try:
        result = SessionCartService.update_item(
            session_id=request.session_id,
            line_id=request.line_id,
            quantity=request.quantity,
        )
        _raise_for_failure(result, "Unable to update cart item.")
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to update cart item: {str(exc)}",
        ) from exc


@router.post("/items/remove")
def remove_cart_item(request: RemoveCartItemRequest):
    try:
        result = SessionCartService.remove_item(
            session_id=request.session_id,
            line_id=request.line_id,
        )
        _raise_for_failure(result, "Unable to remove cart item.")
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to remove cart item: {str(exc)}",
        ) from exc


@router.post("/promotion")
def apply_cart_promotion(request: PromotionRequest):
    try:
        result = SessionCartService.apply_discount(
            session_id=request.session_id,
            discount_code=request.discount_code,
        )

        if result.get("status") in {
            "not_applicable",
            "not_applied",
            "rejected",
        }:
            return result

        _raise_for_failure(result, "Unable to apply promotion.")
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to apply promotion: {str(exc)}",
        ) from exc
