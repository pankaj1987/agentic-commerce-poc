from urllib.parse import unquote

from app.clients.shopify_cart_client import ShopifyCartClient
from app.tools.cart_tools import (
    apply_promotion,
    remove_from_cart,
    update_quantity,
)
from app.tools.product_tools import find_product_variant
from app.security.validation import validate_quantity


class CartService:
    """Application/service layer for Shopify cart operations.

    Responsibilities:
    - Validate incoming cart-related parameters
    - Normalize Shopify cart IDs
    - Resolve customer-facing products to Shopify variants
    - Delegate commerce operations to Shopify/tool layer
    - Return API-friendly results

    The service layer should not contain LLM reasoning.
    """

    @staticmethod
    def _normalize_cart_id(cart_id: str) -> str:
        """Normalize a Shopify cart ID received through an HTTP API.

        Shopify cart IDs look like:

        gid://shopify/Cart/ABC...?key=XYZ

        Because the ID is passed through a URL, characters such as
        ':', '/', '?' and '=' may arrive URL encoded.

        Example:

        gid%3A%2F%2Fshopify%2FCart%2FABC%3Fkey%3DXYZ

        becomes:

        gid://shopify/Cart/ABC?key=XYZ
        """
        if not cart_id:
            raise ValueError("Cart ID is required.")

        normalized_cart_id = unquote(cart_id).strip()

        if not normalized_cart_id:
            raise ValueError("Cart ID is required.")

        return normalized_cart_id

    # ------------------------------------------------------------------
    # CREATE CART
    # ------------------------------------------------------------------

    @staticmethod
    def create_cart() -> dict:
        """Create a new Shopify cart."""
        client = ShopifyCartClient()
        cart = client.create_cart()

        if not cart:
            return {
                "success": False,
                "message": "Unable to create cart.",
            }

        return {
            "success": True,
            "cart": cart,
        }

    # ------------------------------------------------------------------
    # GET CART
    # ------------------------------------------------------------------

    @staticmethod
    def get_cart(cart_id: str) -> dict:
        """Retrieve a Shopify cart by cart ID."""
        try:
            cart_id = CartService._normalize_cart_id(cart_id)
        except ValueError as exc:
            return {
                "success": False,
                "message": str(exc),
            }

        client = ShopifyCartClient()
        cart = client.get_cart(cart_id)

        if cart is None:
            return {
                "success": False,
                "message": "Cart not found.",
            }

        return {
            "success": True,
            "cart": cart,
        }

    # ------------------------------------------------------------------
    # ADD TO CART
    # ------------------------------------------------------------------

    @staticmethod
    def add_to_cart(
        cart_id: str,
        variant_id: str,
        quantity: int,
    ) -> dict:
        """Add an already-resolved Shopify product variant to an existing

        Shopify cart.
        """
        # Validate cart ID
        try:
            cart_id = CartService._normalize_cart_id(cart_id)
        except ValueError as exc:
            return {
                "success": False,
                "message": str(exc),
            }

        # Validate variant
        if not variant_id or not variant_id.strip():
            return {
                "success": False,
                "message": "Product variant ID is required.",
            }

        # Validate quantity at the deterministic service boundary.
        try:
            quantity = validate_quantity(int(quantity))
        except (TypeError, ValueError) as exc:
            return {
                "success": False,
                "message": str(exc),
            }

        client = ShopifyCartClient()
        cart = client.add_to_cart(
            cart_id=cart_id,
            variant_id=variant_id.strip(),
            quantity=quantity,
        )

        if not cart:
            return {
                "success": False,
                "message": "Unable to add product to cart.",
            }

        return {
            "success": True,
            "cart": cart,
        }

    # ------------------------------------------------------------------
    # REMOVE CART ITEM
    # ------------------------------------------------------------------

    @staticmethod
    def remove_item(
        cart_id: str,
        line_id: str,
    ) -> dict:
        """Remove a cart line from Shopify."""
        try:
            cart_id = CartService._normalize_cart_id(cart_id)
        except ValueError as exc:
            return {
                "success": False,
                "message": str(exc),
            }

        if not line_id:
            return {
                "success": False,
                "message": "Cart line ID is required.",
            }

        return remove_from_cart.invoke(
            {
                "cart_id": cart_id,
                "line_id": line_id,
            }
        )

    # ------------------------------------------------------------------
    # UPDATE CART ITEM QUANTITY
    # ------------------------------------------------------------------

    @staticmethod
    def update_item(
        cart_id: str,
        line_id: str,
        quantity: int,
    ) -> dict:
        """Update the quantity of an existing Shopify cart line."""
        try:
            cart_id = CartService._normalize_cart_id(cart_id)
        except ValueError as exc:
            return {
                "success": False,
                "message": str(exc),
            }

        if not line_id:
            return {
                "success": False,
                "message": "Cart line ID is required.",
            }

        try:
            quantity = validate_quantity(int(quantity))
        except (TypeError, ValueError) as exc:
            return {
                "success": False,
                "message": str(exc),
            }

        return update_quantity.invoke(
            {
                "cart_id": cart_id,
                "line_id": line_id,
                "quantity": quantity,
            }
        )

    # ------------------------------------------------------------------
    # APPLY PROMOTION
    # ------------------------------------------------------------------

    @staticmethod
    def apply_discount(
        cart_id: str,
        discount_code: str,
    ) -> dict:
        """Apply a Shopify discount code to the cart."""
        try:
            cart_id = CartService._normalize_cart_id(cart_id)
        except ValueError as exc:
            return {
                "success": False,
                "message": str(exc),
            }

        if not discount_code or not discount_code.strip():
            return {
                "success": False,
                "message": "Discount code is required.",
            }

        discount_code = discount_code.strip()

        return apply_promotion.invoke(
            {
                "cart_id": cart_id,
                "discount_code": discount_code,
            }
        )