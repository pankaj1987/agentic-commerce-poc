from __future__ import annotations

from app.clients.shopify_order_client import ShopifyOrderClient
from app.security.authorization import AuthorizationService
from app.security.context import SecurityContext


def _public_order(order: dict) -> dict:
    """Remove customer PII/internal ownership fields from API/agent responses."""
    result = dict(order)
    result.pop("email", None)
    result.pop("shipping_address", None)
    result.pop("customer", None)
    result.pop("customer_id", None)
    return result


class OrderService:
    @staticmethod
    def _authorize_owned_order(context: SecurityContext, action: str, order: dict) -> None:
        AuthorizationService.authorize_tool(
            context,
            action,
            resource_shopify_customer_id=order.get("customer_id"),
        )

    @staticmethod
    def lookup(order_number: str, security_context: SecurityContext) -> dict:
        order = ShopifyOrderClient().get_order_by_name(order_number)
        if not order:
            return {"success": False, "message": f"Order {order_number} was not found."}
        OrderService._authorize_owned_order(security_context, "lookup_order", order)
        return {"success": True, "order": _public_order(order)}

    @staticmethod
    def history(security_context: SecurityContext, limit: int = 10) -> dict:
        AuthorizationService.authorize_tool(security_context, "get_order_history")
        orders = ShopifyOrderClient().get_order_history_by_customer_id(
            security_context.shopify_customer_id,
            limit,
        )
        return {"success": True, "orders": [_public_order(o) for o in orders]}

    @staticmethod
    def cancellation_eligibility(order_number: str, security_context: SecurityContext) -> dict:
        client = ShopifyOrderClient()
        order = client.get_order_by_name(order_number)
        if not order:
            return {"found": False, "message": f"Order {order_number} was not found."}
        OrderService._authorize_owned_order(
            security_context,
            "check_order_cancellation_eligibility",
            order,
        )
        result = client.get_cancellation_facts(order_number)
        if result.get("order"):
            result["order"] = _public_order(result["order"])
        return result

    @staticmethod
    def return_eligibility(order_number: str, security_context: SecurityContext) -> dict:
        client = ShopifyOrderClient()
        order = client.get_order_by_name(order_number)
        if not order:
            return {"found": False, "message": f"Order {order_number} was not found."}
        OrderService._authorize_owned_order(
            security_context,
            "check_order_return_eligibility",
            order,
        )
        result = client.get_return_facts(order_number)
        if result.get("order"):
            result["order"] = _public_order(result["order"])
        return result
