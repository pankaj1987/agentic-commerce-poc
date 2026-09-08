from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.schemas.cart_schemas import (
    AddCartItemRequest,
    PromotionRequest,
    RemoveCartItemRequest,
    SessionCartRequest,
    UpdateCartItemRequest,
)
from app.security.auth import get_security_context
from app.security.context import SecurityContext
from app.security.authorization import AuthorizationService
from app.services.session_cart_service import SessionCartService

router = APIRouter()


def _raise_for_failure(result: dict, default_message: str) -> None:
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message", default_message))


def _permission_status(exc: Exception) -> int:
    return status.HTTP_403_FORBIDDEN if isinstance(exc, PermissionError) else status.HTTP_400_BAD_REQUEST


@router.post("", status_code=status.HTTP_201_CREATED)
def create_or_restore_cart(
    request: SessionCartRequest | None = None,
    security_context: SecurityContext = Depends(get_security_context),
):
    try:
        AuthorizationService.authorize_tool(security_context, "create_cart")
        result = SessionCartService.initialize_cart(
            request.session_id if request else None,
            user_id=security_context.user_id,
        )
        _raise_for_failure(result, "Unable to initialize cart.")
        return result
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=_permission_status(exc), detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to initialize cart.") from exc


@router.get("")
def get_cart(
    session_id: str = Query(..., min_length=1, max_length=128),
    security_context: SecurityContext = Depends(get_security_context),
):
    try:
        AuthorizationService.authorize_tool(security_context, "get_cart")
        result = SessionCartService.get_cart(session_id, user_id=security_context.user_id)
        if not result.get("success"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("message", "Cart not found."))
        return result
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=_permission_status(exc), detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to retrieve cart.") from exc


@router.post("/items")
def add_cart_item(request: AddCartItemRequest, security_context: SecurityContext = Depends(get_security_context)):
    try:
        AuthorizationService.authorize_tool(security_context, "add_to_cart")
        result = SessionCartService.add_item(
            session_id=request.session_id,
            variant_id=request.variant_id,
            quantity=request.quantity,
            user_id=security_context.user_id,
        )
        _raise_for_failure(result, "Unable to add item to cart.")
        return result
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=_permission_status(exc), detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to add item to cart.") from exc


@router.patch("/items")
def update_cart_item(request: UpdateCartItemRequest, security_context: SecurityContext = Depends(get_security_context)):
    try:
        AuthorizationService.authorize_tool(security_context, "update_quantity")
        result = SessionCartService.update_item(
            session_id=request.session_id,
            line_id=request.line_id,
            quantity=request.quantity,
            user_id=security_context.user_id,
        )
        _raise_for_failure(result, "Unable to update cart item.")
        return result
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=_permission_status(exc), detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to update cart item.") from exc


@router.post("/items/remove")
def remove_cart_item(request: RemoveCartItemRequest, security_context: SecurityContext = Depends(get_security_context)):
    try:
        AuthorizationService.authorize_tool(security_context, "remove_from_cart")
        result = SessionCartService.remove_item(
            session_id=request.session_id,
            line_id=request.line_id,
            user_id=security_context.user_id,
        )
        _raise_for_failure(result, "Unable to remove cart item.")
        return result
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=_permission_status(exc), detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to remove cart item.") from exc


@router.post("/promotion")
def apply_cart_promotion(request: PromotionRequest, security_context: SecurityContext = Depends(get_security_context)):
    try:
        AuthorizationService.authorize_tool(security_context, "apply_discount_code")
        result = SessionCartService.apply_discount(
            session_id=request.session_id,
            discount_code=request.discount_code,
            user_id=security_context.user_id,
        )
        if result.get("status") in {"not_applicable", "not_applied", "rejected"}:
            return result
        _raise_for_failure(result, "Unable to apply promotion.")
        return result
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=_permission_status(exc), detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to apply promotion.") from exc
