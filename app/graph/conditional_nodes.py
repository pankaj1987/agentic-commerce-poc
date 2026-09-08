# app/graph/conditional_nodes.py

import logging

from pydantic import (
    BaseModel,
    Field,
)

from app.clients.shopify_client import (
    ShopifyClient,
)
from app.config.llm import get_llm
from app.graph.state import CommerceState
from app.tools.cart_tools import (
    add_to_cart,
    create_cart,
)


logger = logging.getLogger(__name__)


# ============================================================
# STRUCTURED REQUEST
# ============================================================


class ConditionalInventoryAddRequest(
    BaseModel
):

    product_name: str = Field(
        description=(
            "Customer-facing product name."
        )
    )

    variant_title: str | None = Field(
        default=None,
        description=(
            "Requested variant information such as "
            "'US 8 / Black'."
        ),
    )

    quantity: int = Field(
        default=1,
        ge=1,
        description=(
            "Quantity that should be added if enough "
            "inventory exists."
        ),
    )


# ============================================================
# STEP 1 - EXTRACT REQUEST
# ============================================================


def extract_conditional_inventory_request(
    state: CommerceState,
) -> dict:

    logger.info(
        "Executing conditional inventory request extraction."
    )

    user_message = (
        state.get(
            "user_message",
            "",
        )
        .strip()
    )

    if not user_message:
        return {
            "error": (
                "No conditional inventory request "
                "was provided."
            )
        }

    llm = get_llm()

    structured_llm = (
        llm.with_structured_output(
            ConditionalInventoryAddRequest
        )
    )

    prompt = f"""
Extract the product information from this conditional
e-commerce request.

Customer request:

{user_message}

Extract:

- product_name
- variant_title
- quantity

The quantity represents how many units should be added
to the cart IF sufficient inventory is available.

Rules:

- product_name must contain only the product name.
- variant_title contains size/color/variant information.
- Do not invent product attributes.
- Do not invent quantity.
- If quantity is not explicitly specified, use 1.

Example:

Customer:
"Check whether Athletic Running Shoes US 8 / Black
is in stock. If it is, add 2 to my cart."

Output meaning:

product_name = "Athletic Running Shoes"
variant_title = "US 8 / Black"
quantity = 2
"""

    try:

        result = structured_llm.invoke(
            prompt
        )

    except Exception:

        logger.exception(
            "Conditional inventory extraction failed."
        )

        return {
            "error": (
                "Unable to understand the conditional "
                "inventory request."
            )
        }

    return {
        "product_name": (
            result.product_name
        ),
        "variant_title": (
            result.variant_title
        ),
        "quantity": (
            result.quantity
        ),
    }


# ============================================================
# STEP 2 - RESOLVE EXACT SHOPIFY VARIANT
# ============================================================


def resolve_conditional_variant_node(
    state: CommerceState,
) -> dict:

    logger.info(
        "Resolving variant for conditional inventory workflow."
    )

    product_name = state.get(
        "product_name"
    )

    variant_title = state.get(
        "variant_title"
    )

    if not product_name:
        return {
            "error": (
                "Product name was not identified."
            )
        }

    client = ShopifyClient()

    try:

        result = (
            client.find_product_variant(
                product_name,
                variant_title,
            )
        )

    except Exception:

        logger.exception(
            "Conditional variant resolution failed."
        )

        return {
            "error": (
                "Unable to resolve the requested "
                "product variant."
            )
        }

    if not result:
        return {
            "error": (
                "Product variant could not be resolved."
            )
        }

    if result.get(
        "multiple_matches"
    ):
        return {
            "error": (
                "Multiple products matched the request. "
                "Please specify the exact product."
            )
        }

    if not result.get(
        "found"
    ):
        return {
            "error": result.get(
                "message",
                (
                    "The requested product variant "
                    "could not be found."
                ),
            )
        }

    variant_id = result.get(
        "variant_id"
    )

    if not variant_id:
        return {
            "error": (
                "The product was found, but an exact "
                "variant could not be resolved."
            )
        }

    return {
        "resolved_variant_id": (
            variant_id
        ),
        "product_name": (
            result.get(
                "product_title",
                product_name,
            )
        ),
        "variant_title": (
            result.get(
                "variant_title",
                variant_title,
            )
        ),
    }


# ============================================================
# STEP 3 - CHECK LIVE INVENTORY
# ============================================================


def conditional_inventory_check_node(
    state: CommerceState,
) -> dict:

    logger.info(
        "Executing deterministic inventory condition check."
    )

    variant_id = state.get(
        "resolved_variant_id"
    )

    quantity = (
        state.get(
            "quantity",
            1,
        )
        or 1
    )

    if not variant_id:
        return {
            "error": (
                "Product variant was not resolved."
            )
        }

    client = ShopifyClient()

    try:

        inventory = (
            client.check_inventory(
                variant_id
            )
        )

    except Exception:

        logger.exception(
            "Inventory condition check failed."
        )

        return {
            "error": (
                "Unable to check current inventory."
            )
        }

    tracked = inventory.get(
        "tracked"
    )

    # If Shopify does not track this inventory, do not make
    # a stock-based mutation because the requested condition
    # cannot be verified reliably.
    if tracked is False:

        return {
            "inventory_checked": True,
            "inventory_tracked": False,
            "inventory_available": False,
            "available_quantity": None,
        }

    locations = (
        inventory.get(
            "locations",
            [],
        )
        or []
    )

    total_available = sum(
        max(
            int(
                location.get(
                    "available",
                    0,
                )
                or 0
            ),
            0,
        )
        for location in locations
    )

    enough_inventory = (
        total_available >= quantity
    )

    logger.info(
        (
            "Conditional inventory result. "
            "requested=%s available=%s sufficient=%s"
        ),
        quantity,
        total_available,
        enough_inventory,
    )

    return {
        "inventory_checked": True,
        "inventory_tracked": True,
        "inventory_available": (
            enough_inventory
        ),
        "available_quantity": (
            total_available
        ),
    }


# ============================================================
# CONDITIONAL EDGE
# ============================================================


def route_after_inventory_check(
    state: CommerceState,
) -> str:

    if state.get(
        "error"
    ):
        return "error"

    if (
        state.get(
            "inventory_available"
        )
        is True
    ):
        return "available"

    return "unavailable"


# ============================================================
# STEP 4A - INVENTORY AVAILABLE -> ADD
# ============================================================


def conditional_add_cart_node(
    state: CommerceState,
) -> dict:

    logger.info(
        "Inventory condition passed. Executing cart mutation."
    )

    cart_id = state.get(
        "cart_id"
    )

    # Lazy cart creation. The inventory check is allowed to run with
    # cart_id=None. Only after the condition succeeds do we create a cart.
    if not cart_id:
        create_result = create_cart.invoke({})

        if not create_result.get("success"):
            return {
                "response": create_result.get(
                    "message",
                    "The product is available, but a shopping cart could not be created.",
                ),
                "cart_changed": False,
            }

        created_cart = create_result.get("cart") or {}
        cart_id = created_cart.get("id")

        if not cart_id:
            return {
                "response": (
                    "The product is available, but a shopping cart "
                    "could not be created."
                ),
                "cart_changed": False,
            }

    variant_id = state.get(
        "resolved_variant_id"
    )

    if not variant_id:
        return {
            "response": (
                "The product variant could not be resolved."
            ),
            "cart_changed": False,
        }

    quantity = (
        state.get(
            "quantity",
            1,
        )
        or 1
    )

    result = add_to_cart.invoke(
        {
            "cart_id": cart_id,
            "variant_id": variant_id,
            "quantity": quantity,
        }
    )

    if not result.get(
        "success"
    ):
        return {
            "response": result.get(
                "message",
                (
                    "The product was available, but it "
                    "could not be added to the cart."
                ),
            ),
            "cart_changed": False,
        }

    product_name = (
        state.get(
            "product_name"
        )
        or "Product"
    )

    variant_title = (
        state.get(
            "variant_title"
        )
    )

    available_quantity = (
        state.get(
            "available_quantity"
        )
    )

    product_label = product_name

    if variant_title:
        product_label += (
            f" ({variant_title})"
        )

    if available_quantity is not None:

        availability_text = (
            f"{product_label} is in stock "
            f"with {available_quantity} unit(s) available."
        )

    else:

        availability_text = (
            f"{product_label} is available."
        )

    return {
        "response": (
            f"{availability_text}\n\n"
            f"Added {quantity} "
            f"{product_label} to your cart."
        ),
        # Propagate a lazily-created cart ID to the outer graph so the
        # application session can own the Shopify cart from this point on.
        "cart_id": cart_id,
        "cart_changed": True,
    }


# ============================================================
# STEP 4B - INVENTORY NOT AVAILABLE -> STOP
# ============================================================


def conditional_inventory_unavailable_node(
    state: CommerceState,
) -> dict:

    product_name = (
        state.get(
            "product_name"
        )
        or "Product"
    )

    variant_title = (
        state.get(
            "variant_title"
        )
    )

    quantity = (
        state.get(
            "quantity",
            1,
        )
        or 1
    )

    tracked = state.get(
        "inventory_tracked"
    )

    available_quantity = (
        state.get(
            "available_quantity"
        )
    )

    product_label = product_name

    if variant_title:
        product_label += (
            f" ({variant_title})"
        )

    if tracked is False:

        response = (
            f"Shopify does not track inventory for "
            f"{product_label}, so I could not verify the "
            f"stock condition. I did not add the item "
            f"to your cart."
        )

    elif available_quantity is not None:

        response = (
            f"{product_label} currently has "
            f"{available_quantity} unit(s) available. "
            f"You requested {quantity}, so I did not "
            f"add the item to your cart."
        )

    else:

        response = (
            f"{product_label} does not have sufficient "
            f"verified inventory. I did not add the item "
            f"to your cart."
        )

    return {
        "response": response,
        "cart_changed": False,
    }