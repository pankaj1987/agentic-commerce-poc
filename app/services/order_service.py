from app.clients.shopify_order_client import ShopifyOrderClient


class OrderService:
    @staticmethod
    def lookup(order_number: str) -> dict:
        order = ShopifyOrderClient().get_order_by_name(order_number)
        if not order:
            return {"success": False, "message": f"Order {order_number} was not found."}
        return {"success": True, "order": order}

    @staticmethod
    def history(customer_email: str, limit: int = 10) -> dict:
        orders = ShopifyOrderClient().get_order_history(customer_email, limit)
        return {"success": True, "orders": orders, "customer_email": customer_email}

    @staticmethod
    def cancellation_eligibility(order_number: str) -> dict:
        return ShopifyOrderClient().get_cancellation_facts(order_number)

    @staticmethod
    def return_eligibility(order_number: str) -> dict:
        return ShopifyOrderClient().get_return_facts(order_number)
