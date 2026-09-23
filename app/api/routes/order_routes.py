from fastapi import APIRouter, Depends, HTTPException, Query

from app.security.auth import get_security_context
from app.security.context import SecurityContext
from app.services.order_service import OrderService
from app.security.validation import validate_order_number

router = APIRouter()


def _translate(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=502, detail="Unable to process Shopify order request.")


@router.get("/{order_number}")
def get_order(order_number: str, security_context: SecurityContext = Depends(get_security_context)):
    try:
        result = OrderService.lookup(validate_order_number(order_number), security_context)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise _translate(exc) from exc


@router.get("")
def get_order_history(
    limit: int = Query(default=10, ge=1, le=20),
    security_context: SecurityContext = Depends(get_security_context),
):
    try:
        return OrderService.history(security_context, limit)
    except Exception as exc:
        raise _translate(exc) from exc


@router.get("/{order_number}/cancellation-eligibility")
def cancellation_eligibility(order_number: str, security_context: SecurityContext = Depends(get_security_context)):
    try:
        return OrderService.cancellation_eligibility(validate_order_number(order_number), security_context)
    except Exception as exc:
        raise _translate(exc) from exc


@router.get("/{order_number}/return-eligibility")
def return_eligibility(order_number: str, security_context: SecurityContext = Depends(get_security_context)):
    try:
        return OrderService.return_eligibility(validate_order_number(order_number), security_context)
    except Exception as exc:
        raise _translate(exc) from exc
