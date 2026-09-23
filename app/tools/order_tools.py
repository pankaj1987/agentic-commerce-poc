from langchain_core.tools import tool

from app.clients.shopify_order_client import ShopifyOrderClient
from app.security.context import get_current_security_context
from app.security.tool_authorization import authorize_current_tool
from app.security.validation import validate_order_number


def _public_order(order: dict) -> dict:
    result = dict(order)
    result.pop("email", None)
    result.pop("shipping_address", None)
    result.pop("customer", None)
    result.pop("customer_id", None)
    return result


def _load_owned_order(order_number: str, action: str) -> dict | None:
    order_number = validate_order_number(order_number)
    order = ShopifyOrderClient().get_order_by_name(order_number)
    if not order:
        return None
    authorize_current_tool(action, resource_shopify_customer_id=order.get("customer_id"))
    return order


@tool
def lookup_order(order_number: str) -> dict:
    """Look up an order owned by the authenticated Shopify customer."""
    order = _load_owned_order(order_number, "lookup_order")
    if not order:
        return {"found": False, "message": f"Order {order_number} was not found."}
    return {"found": True, "order": _public_order(order)}


@tool
def get_order_status(order_number: str) -> dict:
    """Get status for an order owned by the authenticated customer."""
    order = _load_owned_order(order_number, "get_order_status")
    if not order:
        return {"found": False, "message": f"Order {order_number} was not found."}
    return {
        "found": True,
        "order_number": order["name"],
        "financial_status": order["financial_status"],
        "fulfillment_status": order["fulfillment_status"],
        "cancelled_at": order["cancelled_at"],
        "return_status": order["return_status"],
        "fulfillments": order["fulfillments"],
    }


@tool
def get_order_details(order_number: str) -> dict:
    """Get detailed live Shopify information for an owned order."""
    order = _load_owned_order(order_number, "get_order_details")
    if not order:
        return {"found": False, "message": f"Order {order_number} was not found."}
    return {"found": True, "order": _public_order(order)}


@tool
def get_order_history(limit: int = 10) -> dict:
    """Get recent orders for the authenticated customer's Shopify customer ID. Never request email from the user."""
    context = get_current_security_context(required=True)
    authorize_current_tool("get_order_history")
    orders = ShopifyOrderClient().get_order_history_by_customer_id(
        context.shopify_customer_id,
        max(1, min(limit, 20)),
    )
    return {"found": bool(orders), "orders": [_public_order(order) for order in orders]}


@tool
def check_order_cancellation_eligibility(order_number: str) -> dict:
    """Check cancellation eligibility for an owned order. Does NOT cancel it."""
    order = _load_owned_order(order_number, "check_order_cancellation_eligibility")
    if not order:
        return {"found": False, "message": f"Order {order_number} was not found."}
    result = ShopifyOrderClient().get_cancellation_facts(order_number)
    if result.get("order"):
        result["order"] = _public_order(result["order"])
    return result


@tool
def check_order_return_eligibility(order_number: str) -> dict:
    """Check return eligibility for an owned order. Does NOT create a return."""
    order = _load_owned_order(order_number, "check_order_return_eligibility")
    if not order:
        return {"found": False, "message": f"Order {order_number} was not found."}
    result = ShopifyOrderClient().get_return_facts(order_number)
    if result.get("order"):
        result["order"] = _public_order(result["order"])
    return result
