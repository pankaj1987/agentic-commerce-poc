from langchain_core.tools import tool

from app.clients.shopify_cart_client import ShopifyCartClient
from app.security.tool_authorization import authorize_current_tool
from app.security.validation import validate_quantity


@tool
def create_cart() -> dict:
    """Create a new shopping cart.

    Returns:
        Newly created Shopify cart information.
    """
    authorize_current_tool("create_cart")
    client = ShopifyCartClient()
    cart = client.create_cart()

    return {
        "success": True,
        "cart": cart,
    }


@tool
def get_cart(cart_id: str) -> dict:
    """Get the current Shopify cart.

    Args:
        cart_id: Shopify cart ID.

    Returns:
        Standardized cart-tool response with success flag
        and the current Shopify cart payload.
    """
    authorize_current_tool("get_cart")
    client = ShopifyCartClient()
    cart = client.get_cart(cart_id)

    if cart is None:
        return {
            "success": False,
            "found": False,
            "message": "Cart not found.",
            "cart": None,
        }

    return {
        "success": True,
        "found": True,
        "cart": cart,
    }


@tool
def add_to_cart(
    cart_id: str,
    variant_id: str,
    quantity: int = 1,
) -> dict:
    """Add a product variant to the Shopify cart.

    Args:
        cart_id: Shopify cart ID.
        variant_id: Shopify product variant ID.
        quantity: Quantity to add.
    """
    authorize_current_tool("add_to_cart")
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
        variant_id=variant_id,
        quantity=quantity,
    )

    return {
        "success": True,
        "cart": cart,
    }


@tool
def calculate_cart(cart_id: str) -> dict:
    """Retrieve the current calculated cart totals from Shopify."""
    authorize_current_tool("calculate_cart")
    client = ShopifyCartClient()
    cart = client.get_cart(cart_id)

    if cart is None:
        return {
            "success": False,
            "message": "Cart not found.",
        }

    return {
        "success": True,
        "cart_id": cart["id"],
        "total_quantity": cart["totalQuantity"],
        "discount_codes": cart.get("discountCodes", []),
        "cost": cart["cost"],
    }


@tool
def remove_from_cart(
    cart_id: str,
    line_id: str,
) -> dict:
    """Remove a cart line from the Shopify cart.

    Args:
        cart_id: Shopify cart ID.
        line_id: Shopify cart line ID.
    """
    authorize_current_tool("remove_from_cart")
    client = ShopifyCartClient()
    cart = client.remove_from_cart(
        cart_id=cart_id,
        line_id=line_id,
    )

    return {
        "success": True,
        "cart": cart,
    }


@tool
def update_quantity(
    cart_id: str,
    quantity: int,
    line_id: str | None = None,
    line_number: int | None = None,
    product_name: str | None = None,
    product_id: str | None = None,
    variant_id: str | None = None,
    variant_title: str | None = None,
) -> dict:
    """Update the quantity of an existing item in the Shopify cart.

    The cart item can be identified using any one or more of:
    - Shopify cart line ID
    - visible cart line number, starting from 1
    - product name
    - Shopify product ID
    - Shopify variant ID
    - variant title such as "US 8 / Black"

    Use this tool for requests such as:
    - Change Athletic Running Shoes quantity to 3
    - Change Athletic Running Shoes (US 8 / Black) to 3
    - Change line 2 to quantity 3
    - Change product gid://shopify/Product/... to quantity 3
    - Change variant gid://shopify/ProductVariant/... to quantity 3

    Args:
        cart_id: Complete Shopify cart ID.
        quantity: New quantity.
        line_id: Optional exact Shopify cart line ID.
        line_number: Optional 1-based line number from the current cart.
        product_name: Optional product title/name.
        product_id: Optional Shopify product ID.
        variant_id: Optional Shopify product variant ID.
        variant_title: Optional variant title, for example "US 8 / Black".

    Returns:
        Updated Shopify cart when exactly one cart line can be identified.
    """
    authorize_current_tool("update_quantity")
    if not cart_id or not cart_id.strip():
        return {
            "success": False,
            "message": "Cart ID is required.",
        }

    try:
        quantity = validate_quantity(int(quantity))
    except (TypeError, ValueError) as exc:
        return {
            "success": False,
            "message": str(exc) + " Use remove_from_cart to remove an item.",
        }

    client = ShopifyCartClient()

    # 1. Exact line ID supplied
    if line_id:
        cart = client.update_quantity(
            cart_id=cart_id,
            line_id=line_id,
            quantity=quantity,
        )

        if cart is None:
            return {
                "success": False,
                "message": "Unable to update the cart item.",
            }

        return {
            "success": True,
            "cart": cart,
        }

    # 2. Load current cart to resolve requested line deterministically
    current_cart = client.get_cart(cart_id)

    if current_cart is None:
        return {
            "success": False,
            "message": "Cart not found.",
        }

    raw_lines = current_cart.get("lines", [])

    if isinstance(raw_lines, dict):
        if isinstance(raw_lines.get("nodes"), list):
            cart_lines = raw_lines["nodes"]
        elif isinstance(raw_lines.get("edges"), list):
            cart_lines = [
                edge.get("node", {})
                for edge in raw_lines["edges"]
            ]
        else:
            cart_lines = []
    elif isinstance(raw_lines, list):
        cart_lines = raw_lines
    else:
        cart_lines = []

    if not cart_lines:
        return {
            "success": False,
            "message": "The cart is empty.",
        }

    # 3. Resolve by visible line number
    if line_number is not None:
        if line_number <= 0:
            return {
                "success": False,
                "message": "Cart line number must start from 1.",
            }

        if line_number > len(cart_lines):
            return {
                "success": False,
                "message": f"Cart line {line_number} does not exist.",
            }

        selected_line = cart_lines[line_number - 1]
        selected_line_id = selected_line.get("id")

        if not selected_line_id:
            return {
                "success": False,
                "message": (
                    "The selected cart line does not contain "
                    "a Shopify line ID."
                ),
            }

        cart = client.update_quantity(
            cart_id=cart_id,
            line_id=selected_line_id,
            quantity=quantity,
        )

        return {
            "success": cart is not None,
            "cart": cart,
            "message": (
                None if cart is not None else "Unable to update the cart item."
            ),
        }

    # 4. Resolve by product / variant information
    if not any([product_name, product_id, variant_id, variant_title]):
        return {
            "success": False,
            "message": (
                "Provide a cart line ID, cart line number, "
                "product name, product ID, variant ID, "
                "or variant title."
            ),
        }

    matching_lines = []

    for cart_line in cart_lines:
        merchandise = cart_line.get("merchandise", {}) or {}
        product = merchandise.get("product", {}) or {}

        current_product_name = (
            product.get("title")
            or cart_line.get("title")
            or ""
        )
        current_product_id = product.get("id") or ""
        current_variant_id = (
            merchandise.get("id")
            or cart_line.get("variant_id")
            or ""
        )
        current_variant_title = (
            merchandise.get("title")
            or cart_line.get("variant_title")
            or ""
        )

        matches = True

        if product_name:
            matches = (
                matches
                and product_name.strip().lower()
                in current_product_name.strip().lower()
            )

        if product_id:
            matches = (
                matches
                and product_id.strip() == current_product_id.strip()
            )

        if variant_id:
            matches = (
                matches
                and variant_id.strip() == current_variant_id.strip()
            )

        if variant_title:
            matches = (
                matches
                and variant_title.strip().lower()
                in current_variant_title.strip().lower()
            )

        if matches:
            matching_lines.append(cart_line)

    # 5. No match
    if not matching_lines:
        return {
            "success": False,
            "status": "item_not_found",
            "message": "No matching item was found in the current cart.",
        }

    # 6. Ambiguous match
    if len(matching_lines) > 1:
        possible_matches = [
            {
                "product_name": (item.get("merchandise", {}) or {}).get("product", {}).get("title"),
                "variant_title": (item.get("merchandise", {}) or {}).get("title"),
                "line_id": item.get("id"),
            }
            for item in matching_lines
        ]

        return {
            "success": False,
            "status": "multiple_matches",
            "message": (
                "Multiple cart items match the request. "
                "Ask the customer to specify the variant or cart line."
            ),
            "matches": possible_matches,
        }

    # 7. Exactly one match → update it
    selected_line = matching_lines[0]
    selected_line_id = selected_line.get("id")

    if not selected_line_id:
        return {
            "success": False,
            "message": (
                "The matching cart item does not contain "
                "a Shopify cart line ID."
            ),
        }

    cart = client.update_quantity(
        cart_id=cart_id,
        line_id=selected_line_id,
        quantity=quantity,
    )

    if cart is None:
        return {
            "success": False,
            "message": "Unable to update the cart item.",
        }

    return {
        "success": True,
        "cart": cart,
    }


@tool
def apply_promotion(
    cart_id: str,
    discount_code: str,
) -> dict:
    """Apply a promotion/discount code to a Shopify cart.

    Args:
        cart_id: Shopify cart ID.
        discount_code: Promotion or discount code provided by the customer.

    Returns:
        Result of applying the promotion, including whether
        Shopify considers the code applicable and the updated
        cart totals.
    """
    authorize_current_tool("apply_discount_code")
    if not discount_code or not discount_code.strip():
        return {
            "success": False,
            "status": "invalid_request",
            "message": "Promotion code cannot be empty.",
        }

    client = ShopifyCartClient()

    cart = client.get_cart(cart_id)
    if cart is None:
        return {
            "success": False,
            "status": "cart_not_found",
            "message": "Cart not found.",
        }

    result = client.apply_discount_code(
        cart_id=cart_id,
        discount_code=discount_code.strip(),
    )

    user_errors = result["user_errors"]
    warnings = result["warnings"]
    updated_cart = result["cart"]

    if user_errors:
        return {
            "success": False,
            "status": "rejected",
            "discount_code": discount_code.strip(),
            "errors": user_errors,
            "warnings": warnings,
        }

    if updated_cart is None:
        return {
            "success": False,
            "status": "failed",
            "discount_code": discount_code.strip(),
            "message": "Shopify did not return an updated cart.",
            "warnings": warnings,
        }

    discount_codes = updated_cart.get("discountCodes", [])

    applied_code = next(
        (
            code
            for code in discount_codes
            if code["code"].lower() == discount_code.strip().lower()
        ),
        None,
    )

    if applied_code is None:
        return {
            "success": False,
            "status": "not_applied",
            "discount_code": discount_code.strip(),
            "message": "The promotion code was not applied to the current cart.",
            "warnings": warnings,
            "cart": updated_cart,
        }

    if not applied_code["applicable"]:
        return {
            "success": False,
            "status": "not_applicable",
            "discount_code": applied_code["code"],
            "message": "The promotion code is not applicable to the current cart.",
            "warnings": warnings,
            "cart": updated_cart,
        }

    return {
        "success": True,
        "status": "applied",
        "discount_code": applied_code["code"],
        "applicable": True,
        "warnings": warnings,
        "cart": updated_cart,
    }