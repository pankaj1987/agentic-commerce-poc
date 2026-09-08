from langchain_core.tools import tool

from app.clients.shopify_order_client import ShopifyOrderClient


@tool
def lookup_order(order_number: str) -> dict:
    """Look up a Shopify order by customer-facing order number/name, e.g. #1001."""
    order = ShopifyOrderClient().get_order_by_name(order_number)
    if not order:
        return {"found": False, "message": f"Order {order_number} was not found."}
    return {"found": True, "order": order}


@tool
def get_order_status(order_number: str) -> dict:
    """Get current financial, fulfillment, delivery/tracking, cancellation and return status for an order."""
    order = ShopifyOrderClient().get_order_by_name(order_number)
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
    """Get detailed live Shopify order information including items, totals and fulfillment details."""
    order = ShopifyOrderClient().get_order_by_name(order_number)
    if not order:
        return {"found": False, "message": f"Order {order_number} was not found."}
    return {"found": True, "order": order}


@tool
def get_order_history(customer_email: str, limit: int = 10) -> dict:
    """Get recent Shopify orders for a customer email. Email is required because Phase 4 has no authenticated customer identity mapping yet."""
    orders = ShopifyOrderClient().get_order_history(customer_email, limit)
    return {"found": bool(orders), "customer_email": customer_email, "orders": orders}


@tool
def check_order_cancellation_eligibility(order_number: str) -> dict:
    """Check read-only transactional facts relevant to cancelling an order. Does NOT cancel the order."""
    return ShopifyOrderClient().get_cancellation_facts(order_number)


@tool
def check_order_return_eligibility(order_number: str) -> dict:
    """Check live transactional facts relevant to returning an order. Combine with search_knowledge for return-policy rules. Does NOT create a return."""
    return ShopifyOrderClient().get_return_facts(order_number)
