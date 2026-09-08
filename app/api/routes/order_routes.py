from fastapi import APIRouter, HTTPException, Query

from app.services.order_service import OrderService


router = APIRouter()


@router.get("/{order_number}")
def get_order(order_number: str):
    try:
        result = OrderService.lookup(order_number)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to retrieve Shopify order.") from exc


@router.get("")
def get_order_history(
    customer_email: str = Query(...),
    limit: int = Query(default=10, ge=1, le=20),
):
    try:
        return OrderService.history(customer_email, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to retrieve Shopify order history.") from exc


@router.get("/{order_number}/cancellation-eligibility")
def cancellation_eligibility(order_number: str):
    try:
        return OrderService.cancellation_eligibility(order_number)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to evaluate cancellation eligibility.") from exc


@router.get("/{order_number}/return-eligibility")
def return_eligibility(order_number: str):
    try:
        return OrderService.return_eligibility(order_number)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to evaluate return eligibility.") from exc
