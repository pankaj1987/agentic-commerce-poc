import re
from typing import Any

from app.clients.shopify_client import ShopifyClient


class ShopifyOrderClient:
    """Read-only Shopify Admin GraphQL adapter for Phase 4 order workflows."""

    def __init__(self) -> None:
        self.client = ShopifyClient()

    @staticmethod
    def _normalize_order_name(order_number: str) -> str:
        value = (order_number or "").strip()
        if not value:
            raise ValueError("Order number is required.")
        if value.lower().startswith("order "):
            value = value[6:].strip()
        # Preserve merchant prefixes/suffixes, but add Shopify's common # prefix
        # for a purely numeric order number.
        if re.fullmatch(r"\d+", value):
            value = f"#{value}"
        return value

    @staticmethod
    def _money(money_bag: dict | None) -> dict | None:
        if not money_bag:
            return None
        money = money_bag.get("shopMoney") or {}
        if not money:
            return None
        return {
            "amount": float(money.get("amount", 0)),
            "currency": money.get("currencyCode"),
        }

    def _order_fields(self) -> str:
        return """
            id
            name
            createdAt
            updatedAt
            cancelledAt
            cancelReason
            displayFinancialStatus
            displayFulfillmentStatus
            refundable
            restockable
            returnStatus
            email
            totalPriceSet { shopMoney { amount currencyCode } }
            currentSubtotalPriceSet { shopMoney { amount currencyCode } }
            currentTotalTaxSet { shopMoney { amount currencyCode } }
            currentTotalDiscountsSet { shopMoney { amount currencyCode } }
            shippingAddress {
                firstName lastName address1 address2 city province zip country
            }
            lineItems(first: 50) {
                nodes {
                    id
                    name
                    title
                    variantTitle
                    sku
                    quantity
                    currentQuantity
                    refundableQuantity
                    unfulfilledQuantity
                    restockable
                    originalUnitPriceSet { shopMoney { amount currencyCode } }
                }
            }
            fulfillments(first: 20) {
                id
                status
                displayStatus
                createdAt
                deliveredAt
                estimatedDeliveryAt
                trackingInfo(first: 10) { company number url }
            }
        """

    def _normalize_order(self, order: dict | None) -> dict | None:
        if not order:
            return None

        line_items = []
        for item in (order.get("lineItems") or {}).get("nodes", []):
            line_items.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "title": item.get("title"),
                "variant_title": item.get("variantTitle"),
                "sku": item.get("sku"),
                "quantity": item.get("quantity"),
                "current_quantity": item.get("currentQuantity"),
                "refundable_quantity": item.get("refundableQuantity"),
                "unfulfilled_quantity": item.get("unfulfilledQuantity"),
                "restockable": item.get("restockable"),
                "unit_price": self._money(item.get("originalUnitPriceSet")),
            })

        fulfillments = []
        for fulfillment in order.get("fulfillments") or []:
            fulfillments.append({
                "id": fulfillment.get("id"),
                "status": fulfillment.get("status"),
                "display_status": fulfillment.get("displayStatus"),
                "created_at": fulfillment.get("createdAt"),
                "delivered_at": fulfillment.get("deliveredAt"),
                "estimated_delivery_at": fulfillment.get("estimatedDeliveryAt"),
                "tracking": fulfillment.get("trackingInfo") or [],
            })

        return {
            "id": order.get("id"),
            "name": order.get("name"),
            "created_at": order.get("createdAt"),
            "updated_at": order.get("updatedAt"),
            "cancelled_at": order.get("cancelledAt"),
            "cancel_reason": order.get("cancelReason"),
            "financial_status": order.get("displayFinancialStatus"),
            "fulfillment_status": order.get("displayFulfillmentStatus"),
            "refundable": order.get("refundable"),
            "restockable": order.get("restockable"),
            "return_status": order.get("returnStatus"),
            "email": order.get("email"),
            "total": self._money(order.get("totalPriceSet")),
            "subtotal": self._money(order.get("currentSubtotalPriceSet")),
            "tax": self._money(order.get("currentTotalTaxSet")),
            "discounts": self._money(order.get("currentTotalDiscountsSet")),
            "shipping_address": order.get("shippingAddress"),
            "line_items": line_items,
            "fulfillments": fulfillments,
        }

    def get_order_by_name(self, order_number: str) -> dict | None:
        name = self._normalize_order_name(order_number)
        query = f"""
        query GetOrderByName($query: String!) {{
            orders(first: 2, query: $query, sortKey: CREATED_AT, reverse: true) {{
                nodes {{ {self._order_fields()} }}
            }}
        }}
        """
        data = self.client.execute_query(query, {"query": f"name:{name}"})
        orders = data["orders"]["nodes"]
        if not orders:
            return None
        # Prefer exact order name if Shopify search returns more than one result.
        for order in orders:
            if (order.get("name") or "").lower() == name.lower():
                return self._normalize_order(order)
        return self._normalize_order(orders[0])

    def get_order_history(self, customer_email: str, first: int = 10) -> list[dict]:
        email = (customer_email or "").strip()
        if not email or "@" not in email:
            raise ValueError("A valid customer email is required for order history.")
        first = max(1, min(first, 20))
        query = f"""
        query GetOrderHistory($query: String!, $first: Int!) {{
            orders(first: $first, query: $query, sortKey: CREATED_AT, reverse: true) {{
                nodes {{ {self._order_fields()} }}
            }}
        }}
        """
        data = self.client.execute_query(
            query,
            {"query": f"email:{email}", "first": first},
        )
        return [
            self._normalize_order(order)
            for order in data["orders"]["nodes"]
        ]

    def get_cancellation_facts(self, order_number: str) -> dict[str, Any]:
        order = self.get_order_by_name(order_number)
        if not order:
            return {"found": False, "message": f"Order {order_number} was not found."}

        reasons: list[str] = []
        candidate = True

        if order.get("cancelled_at"):
            candidate = False
            reasons.append("The order is already cancelled.")

        fulfillment_status = order.get("fulfillment_status")
        if fulfillment_status in {"FULFILLED", "RESTOCKED"}:
            candidate = False
            reasons.append("The order is already fully fulfilled/restocked.")

        if order.get("return_status") not in {None, "NO_RETURN"}:
            candidate = False
            reasons.append(
                f"The order has return status {order.get('return_status')}, so cancellation needs manual review."
            )

        if candidate:
            reasons.append(
                "The order is a cancellation candidate based on the read-only order state. "
                "Final cancellation validity is determined by Shopify when the cancellation mutation is executed."
            )

        return {
            "found": True,
            "order": order,
            "cancellation_candidate": candidate,
            "reasons": reasons,
            "phase4_action": "eligibility_only",
        }

    def get_return_facts(self, order_number: str) -> dict[str, Any]:
        order = self.get_order_by_name(order_number)
        if not order:
            return {"found": False, "message": f"Order {order_number} was not found."}

        delivered_dates = [
            f.get("delivered_at")
            for f in order.get("fulfillments", [])
            if f.get("delivered_at")
        ]
        refundable_items = [
            item for item in order.get("line_items", [])
            if (item.get("refundable_quantity") or 0) > 0
        ]

        candidate = bool(refundable_items) and not order.get("cancelled_at")
        reasons: list[str] = []
        if order.get("cancelled_at"):
            reasons.append("The order is cancelled.")
        if not refundable_items:
            reasons.append("No line item currently has refundable quantity remaining.")
        if candidate:
            reasons.append("The order has at least one line item with refundable quantity remaining.")
        if not delivered_dates:
            reasons.append(
                "Shopify does not currently provide a delivered-at timestamp for this order, "
                "so a delivery-based return window cannot be conclusively calculated from order data alone."
            )

        return {
            "found": True,
            "order": order,
            "return_candidate": candidate,
            "delivered_at": max(delivered_dates) if delivered_dates else None,
            "refundable_items": refundable_items,
            "reasons": reasons,
            "phase4_action": "eligibility_only",
        }
