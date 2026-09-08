# app/graph/cart_nodes.py

import logging

from pydantic import BaseModel, Field

from app.config.llm import get_llm
from app.config.settings import settings
from app.graph.state import CommerceState
from app.security.validation import validate_explicit_cart_quantity, validate_quantity

from app.tools.cart_tools import (
    create_cart,
    get_cart,
    add_to_cart,
    update_quantity,
    remove_from_cart,
    apply_promotion,
)

from app.tools.product_tools import (
    find_product_variant,
)


logger = logging.getLogger(__name__)


# ============================================================
# STRUCTURED OUTPUT MODELS
# ============================================================

class AddCartRequest(BaseModel):
    """
    Structured representation of an add-to-cart request.
    """

    product_name: str = Field(
        description="Customer-facing product name."
    )

    variant_title: str | None = Field(
        default=None,
        description=(
            "Variant information explicitly supplied by "
            "the customer, for example 'US 8 / Black'."
        ),
    )

    quantity: int = Field(
        default=1,
        ge=1,
        le=settings.max_cart_item_quantity,
        description=(
            "Quantity requested by the customer. "
            "Use 1 when quantity is not specified."
        ),
    )


class UpdateCartRequest(BaseModel):
    """
    Structured representation of a cart quantity-update request.
    """

    line_number: int | None = Field(
        default=None,
        ge=1,
        description=(
            "One-based cart line number supplied by the customer."
        ),
    )

    product_name: str | None = Field(
        default=None,
        description=(
            "Product name supplied by the customer."
        ),
    )

    variant_title: str | None = Field(
        default=None,
        description=(
            "Variant information supplied by the customer."
        ),
    )

    quantity: int = Field(
        ge=1,
        le=settings.max_cart_item_quantity,
        description=(
            "New quantity explicitly requested by the customer."
        ),
    )


class RemoveCartRequest(BaseModel):
    """Structured representation of a remove-from-cart request.

    A customer may identify the target by visible cart line number or by
    product/variant description. The actual Shopify line ID is always
    resolved from the live cart, never invented by the LLM.
    """

    line_number: int | None = Field(
        default=None,
        ge=1,
        description="Optional one-based cart line number explicitly supplied by the customer.",
    )
    product_name: str | None = Field(
        default=None,
        description="Optional customer-facing product name to remove.",
    )
    variant_title: str | None = Field(
        default=None,
        description="Optional variant information such as 'US 8 / Black'.",
    )


class PromotionRequest(BaseModel):
    """
    Structured representation of a promotion-code request.
    """

    promotion_code: str = Field(
        min_length=1,
        description=(
            "Promotion, discount, or coupon code explicitly "
            "supplied by the customer."
        ),
    )


# ============================================================
# VIEW CART NODE
# ============================================================

def view_cart_node(
    state: CommerceState,
) -> dict:

    logger.info(
        "Executing view cart node."
    )

    cart_id = state.get(
        "cart_id"
    )

    if not cart_id:
        return {
            "response": (
                "No active shopping cart was found."
            ),
            "cart_changed": False,
        }

    result = get_cart.invoke(
        {
            "cart_id": cart_id,
        }
    )

    if not result.get("success"):
        return {
            "response": result.get(
                "message",
                "Unable to retrieve the cart.",
            ),
            "cart_changed": False,
        }

    cart = result.get(
        "cart"
    )

    if not cart:
        return {
            "response": (
                "Unable to retrieve the cart."
            ),
            "cart_changed": False,
        }

    return {
        "response": format_cart(
            cart
        ),
        "cart_changed": False,
    }


# ============================================================
# CART FORMATTER
# ============================================================

def format_cart(
    cart: dict,
) -> str:

    raw_lines = cart.get(
        "lines",
        []
    )

    if isinstance(raw_lines, dict):
        if isinstance(
            raw_lines.get("nodes"),
            list,
        ):
            lines = raw_lines["nodes"]
        elif isinstance(
            raw_lines.get("edges"),
            list,
        ):
            lines = [
                edge.get("node", {})
                for edge in raw_lines["edges"]
            ]
        else:
            lines = []
    elif isinstance(raw_lines, list):
        lines = raw_lines
    else:
        lines = []

    if not lines:
        return "Your cart is empty."

    output = [
        "Your cart contains:"
    ]

    for index, line in enumerate(
        lines,
        start=1,
    ):
        merchandise = line.get(
            "merchandise",
            {}
        )

        product = merchandise.get(
            "product",
            {}
        )

        product_title = product.get(
            "title",
            "Product",
        )

        variant_title = merchandise.get(
            "title"
        )

        quantity = line.get(
            "quantity",
            0,
        )

        item_text = (
            f"{index}. {product_title}"
        )

        if variant_title:
            item_text += (
                f" ({variant_title})"
            )

        item_text += (
            f" — Qty: {quantity}"
        )

        output.append(
            item_text
        )

    cost = cart.get(
        "cost",
        {}
    )

    subtotal = cost.get(
        "subtotalAmount",
        {}
    )

    total = cost.get(
        "totalAmount",
        {}
    )

    if subtotal:
        amount = subtotal.get(
            "amount"
        )

        currency = subtotal.get(
            "currencyCode"
        )

        if amount and currency:
            output.append(
                f"Subtotal: {amount} {currency}"
            )

    if total:
        amount = total.get(
            "amount"
        )

        currency = total.get(
            "currencyCode"
        )

        if amount and currency:
            output.append(
                f"Total: {amount} {currency}"
            )

    return "\n".join(
        output
    )


# ============================================================
# ADD TO CART - STEP 1
# EXTRACT PRODUCT INFORMATION
# ============================================================

def extract_add_request(
    state: CommerceState,
) -> dict:

    logger.info(
        "Executing add-to-cart request extraction node."
    )

    user_message = state.get(
        "user_message",
        "",
    )

    if not user_message:
        return {
            "error": (
                "No user message was provided."
            )
        }

    # Security/business validation MUST happen before the LLM. Local models
    # can normalize "-2" to 2 or replace 0 with a default quantity, which
    # would bypass a Pydantic constraint applied only after extraction.
    try:
        explicit_quantity = validate_explicit_cart_quantity(user_message)
    except ValueError as exc:
        return {"error": str(exc)}

    llm = get_llm()

    structured_llm = (
        llm.with_structured_output(
            AddCartRequest
        )
    )

    prompt = f"""
You are extracting structured information from an
e-commerce add-to-cart request.

Customer request:

{user_message}

Extract:
- product_name
- variant_title
- quantity

Rules:
- product_name must contain only the product name.
- Put size/color/variant details in variant_title.
- Do not invent product attributes.
- If quantity is not specified, use 1.

Example:

"Add Athletic Running Shoes US 8 / Black to my cart"

product_name = "Athletic Running Shoes"
variant_title = "US 8 / Black"
quantity = 1
"""

    try:
        result = structured_llm.invoke(
            prompt
        )

    except Exception:
        logger.exception(
            "Unable to extract add-to-cart request."
        )

        return {
            "error": (
                "Unable to understand the add-to-cart request."
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
            explicit_quantity if explicit_quantity is not None else result.quantity
        ),
    }


# ============================================================
# ADD TO CART - STEP 2
# RESOLVE SHOPIFY VARIANT
# ============================================================

def resolve_variant_node(
    state: CommerceState,
) -> dict:

    logger.info(
        "Executing product variant resolver node."
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

    tool_input = {
        "product_name": product_name,
    }

    if variant_title:
        tool_input["variant_title"] = (
            variant_title
        )

    result = (
        find_product_variant.invoke(
            tool_input
        )
    )

    logger.info(
        "find_product_variant completed. found=%s multiple_matches=%s",
        result.get("found"),
        result.get("multiple_matches"),
    )

    if result.get("multiple_matches"):
        candidates = result.get(
            "candidates",
            [],
        )

        candidate_names = [
            candidate.get("product_title")
            for candidate in candidates
            if candidate.get("product_title")
        ]

        if candidate_names:
            return {
                "error": (
                    "Multiple products matched the request: "
                    + ", ".join(candidate_names)
                    + ". Please specify the exact product."
                )
            }

        return {
            "error": (
                "Multiple products matched the request. "
                "Please specify the exact product."
            )
        }

    if not result.get("found"):
        return {
            "error": result.get(
                "message",
                "Product variant could not be resolved.",
            )
        }

    variant_id = result.get(
        "variant_id"
    )

    if not variant_id:
        return {
            "error": (
                "A product was found, but an exact Shopify "
                "product variant could not be resolved."
            )
        }

    return {
        "resolved_variant_id": (
            variant_id
        )
    }


# ============================================================
# ADD TO CART - STEP 3
# PERFORM SHOPIFY MUTATION
# ============================================================

def add_cart_node(
    state: CommerceState,
) -> dict:

    logger.info(
        "Executing add-to-cart mutation node."
    )

    cart_id = state.get(
        "cart_id"
    )

    # Lazy cart creation: a session may exist without a Shopify cart.
    # Create the cart only when the customer performs the first ADD.
    if not cart_id:
        create_result = create_cart.invoke({})

        if not create_result.get("success"):
            return {
                "response": create_result.get(
                    "message",
                    "Unable to create a shopping cart.",
                ),
                "cart_changed": False,
            }

        created_cart = create_result.get("cart") or {}
        cart_id = created_cart.get("id")

        if not cart_id:
            return {
                "response": "Unable to create a shopping cart.",
                "cart_changed": False,
            }

    variant_id = state.get(
        "resolved_variant_id"
    )

    if not variant_id:
        return {
            "response": (
                "The requested product variant "
                "could not be resolved."
            ),
            "cart_changed": False,
        }

    quantity = state.get(
        "quantity",
        1,
    )

    if quantity is None:
        quantity = 1

    try:
        quantity = validate_quantity(int(quantity))
    except (TypeError, ValueError) as exc:
        return {
            "response": str(exc),
            "cart_changed": False,
        }

    result = add_to_cart.invoke(
        {
            "cart_id": cart_id,
            "variant_id": variant_id,
            "quantity": quantity,
        }
    )

    if not result.get("success"):
        return {
            "response": result.get(
                "message",
                "Unable to add the product to the cart.",
            ),
            "cart_changed": False,
        }

    product_name = (
        state.get("product_name")
        or "product"
    )

    variant_title = state.get(
        "variant_title"
    )

    product_label = product_name

    if variant_title:
        product_label += (
            f" ({variant_title})"
        )

    return {
        "response": (
            f"Added {quantity} "
            f"{product_label} to your cart."
        ),
        # Propagate a lazily-created cart ID to the outer graph.
        # ChatService persists it against CommerceSession.
        "cart_id": cart_id,
        "cart_changed": True,
    }


# ============================================================
# UPDATE QUANTITY - STEP 1
# EXTRACT UPDATE REQUEST
# ============================================================

def extract_update_request(
    state: CommerceState,
) -> dict:

    logger.info(
        "Executing cart quantity update extraction node."
    )

    user_message = state.get(
        "user_message",
        "",
    )

    if not user_message:
        return {
            "error": (
                "No user message was provided."
            )
        }

    try:
        explicit_quantity = validate_explicit_cart_quantity(user_message)
    except ValueError as exc:
        return {"error": str(exc)}

    llm = get_llm()

    structured_llm = (
        llm.with_structured_output(
            UpdateCartRequest
        )
    )

    prompt = f"""
Extract the cart quantity-update request.

Customer request:

{user_message}

Extract only information explicitly supplied:

- line_number
- product_name
- variant_title
- quantity

Examples:

"Change line 1 quantity to 3"

line_number = 1
product_name = null
variant_title = null
quantity = 3


"Change Athletic Running Shoes to quantity 2"

line_number = null
product_name = "Athletic Running Shoes"
variant_title = null
quantity = 2


"Change Athletic Running Shoes US 8 / Black to 3"

line_number = null
product_name = "Athletic Running Shoes"
variant_title = "US 8 / Black"
quantity = 3

Rules:

- Do not invent product information.
- Do not invent a cart line.
- Do not invent quantity.
"""

    try:
        result = structured_llm.invoke(
            prompt
        )

    except Exception:
        logger.exception(
            "Unable to extract cart quantity update request."
        )

        return {
            "error": (
                "Unable to understand the quantity update request."
            )
        }

    return {
        "line_number": (
            result.line_number
        ),
        "product_name": (
            result.product_name
        ),
        "variant_title": (
            result.variant_title
        ),
        "quantity": (
            explicit_quantity if explicit_quantity is not None else result.quantity
        ),
    }


# ============================================================
# UPDATE QUANTITY - STEP 2
# PERFORM SHOPIFY MUTATION
# ============================================================

def update_cart_node(
    state: CommerceState,
) -> dict:

    logger.info(
        "Executing cart quantity update mutation node."
    )

    cart_id = state.get(
        "cart_id"
    )

    if not cart_id:
        return {
            "response": (
                "No active shopping cart was found."
            ),
            "cart_changed": False,
        }

    quantity = state.get(
        "quantity"
    )

    if quantity is None:
        return {
            "response": (
                "The requested quantity could not be identified."
            ),
            "cart_changed": False,
        }

    try:
        quantity = validate_quantity(int(quantity))
    except (TypeError, ValueError) as exc:
        return {
            "response": str(exc),
            "cart_changed": False,
        }

    tool_input = {
        "cart_id": cart_id,
        "quantity": quantity,
    }

    line_number = state.get(
        "line_number"
    )

    product_name = state.get(
        "product_name"
    )

    variant_title = state.get(
        "variant_title"
    )

    if line_number is not None:
        tool_input["line_number"] = (
            line_number
        )

    if product_name:
        tool_input["product_name"] = (
            product_name
        )

    if variant_title:
        tool_input["variant_title"] = (
            variant_title
        )

    if (
        line_number is None
        and not product_name
    ):
        return {
            "response": (
                "I could not determine which cart item "
                "you want to update."
            ),
            "cart_changed": False,
        }

    result = update_quantity.invoke(
        tool_input
    )

    if not result.get("success"):
        return {
            "response": result.get(
                "message",
                "Unable to update cart quantity.",
            ),
            "cart_changed": False,
        }

    return {
        "response": (
            "Cart quantity updated successfully."
        ),
        "cart_changed": True,
    }


# ============================================================
# REMOVE FROM CART - STEP 1
# EXTRACT LINE NUMBER
# ============================================================

def extract_remove_request(
    state: CommerceState,
) -> dict:
    """Extract a deterministic cart-line selector from a remove request."""

    logger.info("Executing remove-from-cart request extraction node.")
    user_message = state.get("user_message", "")
    if not user_message:
        return {"error": "No user message was provided."}

    llm = get_llm()
    structured_llm = llm.with_structured_output(RemoveCartRequest)
    prompt = f"""
Extract which item the customer wants removed from the live cart.

Customer request:
{user_message}

Return any selector explicitly supplied by the customer:
- line_number when they say e.g. "remove line 2"
- product_name when they identify a product e.g. "remove running shoe"
- variant_title when they identify a variant e.g. "remove Athletic Running Shoes US 8 / Black"

Rules:
- Do not invent a line number.
- Do not invent a Shopify line ID.
- Do not invent product or variant attributes.
- At least one of line_number, product_name, variant_title must come from the request.
"""
    try:
        result = structured_llm.invoke(prompt)
    except Exception:
        logger.exception("Unable to extract remove-from-cart request.")
        return {"error": "Unable to determine which cart item should be removed."}

    if not any([result.line_number, result.product_name, result.variant_title]):
        return {"error": "Unable to determine which cart item should be removed."}

    return {
        "line_number": result.line_number,
        "product_name": result.product_name,
        "variant_title": result.variant_title,
    }


# ============================================================
# REMOVE FROM CART - STEP 2
# RESOLVE LINE NUMBER TO SHOPIFY LINE ID
# ============================================================

def _normalize_match_text(value: str | None) -> list[str]:
    import re
    tokens = re.findall(r"[a-z0-9]+", (value or "").lower())
    # very small normalization so "shoe" matches "shoes" without bringing
    # fuzzy LLM reasoning into a mutation selector.
    return [token[:-1] if token.endswith("s") and len(token) > 3 else token for token in tokens]


def _selector_matches(query: str | None, candidate: str | None) -> bool:
    query_tokens = _normalize_match_text(query)
    candidate_tokens = _normalize_match_text(candidate)
    return bool(query_tokens) and set(query_tokens).issubset(set(candidate_tokens))


def resolve_remove_line_node(state: CommerceState) -> dict:
    """Resolve a user-visible selector to exactly one live Shopify line ID."""
    logger.info("Executing remove cart line resolver node.")
    cart_id = state.get("cart_id")
    if not cart_id:
        return {"response": "No active shopping cart was found.", "cart_changed": False}

    result = get_cart.invoke({"cart_id": cart_id})
    if not result.get("success"):
        return {"response": result.get("message", "Unable to retrieve the cart."), "cart_changed": False}
    cart = result.get("cart") or {}
    raw_lines = cart.get("lines", [])
    if isinstance(raw_lines, dict):
        if isinstance(raw_lines.get("nodes"), list):
            lines = raw_lines["nodes"]
        elif isinstance(raw_lines.get("edges"), list):
            lines = [edge.get("node", {}) for edge in raw_lines["edges"]]
        else:
            lines = []
    elif isinstance(raw_lines, list):
        lines = raw_lines
    else:
        lines = []

    if not lines:
        return {"response": "Your cart is empty.", "cart_changed": False}

    line_number = state.get("line_number")
    if line_number is not None:
        if line_number < 1 or line_number > len(lines):
            return {
                "response": f"Cart line {line_number} does not exist. Your cart currently has {len(lines)} item(s).",
                "cart_changed": False,
            }
        matches = [lines[line_number - 1]]
    else:
        product_name = state.get("product_name")
        variant_title = state.get("variant_title")
        matches = []
        for line in lines:
            merchandise = line.get("merchandise", {}) or {}
            product = merchandise.get("product", {}) or {}
            current_product = product.get("title") or line.get("title") or ""
            current_variant = merchandise.get("title") or line.get("variant_title") or ""
            product_ok = True if not product_name else _selector_matches(product_name, current_product)
            variant_ok = True if not variant_title else _selector_matches(variant_title, current_variant)
            if product_ok and variant_ok:
                matches.append(line)

        if not matches:
            selector = product_name or variant_title or "requested item"
            return {
                "response": f"I could not find {selector} in your current cart.",
                "cart_changed": False,
            }
        if len(matches) > 1:
            labels = []
            for line in matches:
                merchandise = line.get("merchandise", {}) or {}
                product = merchandise.get("product", {}) or {}
                label = product.get("title") or "Product"
                if merchandise.get("title"):
                    label += f" ({merchandise.get('title')})"
                labels.append(label)
            return {
                "response": "Multiple cart items match that description: " + ", ".join(labels) + ". Please specify the variant or cart line number.",
                "cart_changed": False,
            }

    selected_line = matches[0]
    line_id = selected_line.get("id")
    if not line_id:
        return {"response": "Unable to identify the selected cart line.", "cart_changed": False}
    merchandise = selected_line.get("merchandise", {}) or {}
    product = merchandise.get("product", {}) or {}
    logger.info("Cart line resolved successfully for removal.")
    return {
        "line_id": line_id,
        "product_name": product.get("title"),
        "variant_title": merchandise.get("title"),
    }


# ============================================================
# REMOVE FROM CART - STEP 3
# PERFORM SHOPIFY MUTATION
# ============================================================

def remove_cart_node(
    state: CommerceState,
) -> dict:
    """
    Remove the resolved Shopify cart line.
    """

    logger.info(
        "Executing remove-from-cart mutation node."
    )

    cart_id = state.get(
        "cart_id"
    )

    if not cart_id:
        return {
            "response": (
                "No active shopping cart was found."
            ),
            "cart_changed": False,
        }

    line_id = state.get(
        "line_id"
    )

    if not line_id:
        return {
            "response": (
                "The cart line could not be identified."
            ),
            "cart_changed": False,
        }

    result = remove_from_cart.invoke(
        {
            "cart_id": cart_id,
            "line_id": line_id,
        }
    )

    logger.info(
        "remove_from_cart completed. success=%s",
        result.get("success"),
    )

    if not result.get("success"):
        return {
            "response": result.get(
                "message",
                "Unable to remove the item from the cart.",
            ),
            "cart_changed": False,
        }

    product_name = state.get(
        "product_name"
    )

    variant_title = state.get(
        "variant_title"
    )

    if product_name:
        product_label = product_name

        if variant_title:
            product_label += (
                f" ({variant_title})"
            )

        response = (
            f"Removed {product_label} from your cart."
        )

    else:
        response = (
            "Item removed from your cart."
        )

    return {
        "response": response,
        "cart_changed": True,
    }

# ============================================================
# PROMOTION - STEP 1
# EXTRACT PROMOTION CODE
# ============================================================

def extract_promotion_request(
    state: CommerceState,
) -> dict:

    logger.info(
        "Executing promotion request extraction node."
    )

    user_message = state.get(
        "user_message",
        "",
    )

    if not user_message:
        return {
            "error": (
                "No user message was provided."
            )
        }

    llm = get_llm()

    structured_llm = (
        llm.with_structured_output(
            PromotionRequest
        )
    )

    prompt = f"""
Extract the promotion, discount, or coupon code
from the customer's request.

Customer request:

{user_message}

Example:

Customer:
"Apply SAVE20 to my cart"

Output meaning:

promotion_code = "SAVE20"

Rules:

- Extract only the code supplied by the customer.
- Do not invent a promotion code.
- Do not determine whether the promotion is valid.
- Do not calculate any discount.
"""

    try:
        result = structured_llm.invoke(
            prompt
        )

    except Exception:
        logger.exception(
            "Unable to extract promotion code."
        )

        return {
            "error": (
                "Unable to identify the promotion code."
            )
        }

    return {
        "promotion_code": (
            result.promotion_code
        )
    }


# ============================================================
# PROMOTION - STEP 2
# APPLY PROMOTION
# ============================================================

def promotion_node(
    state: CommerceState,
) -> dict:

    logger.info(
        "Executing promotion node."
    )

    cart_id = state.get(
        "cart_id"
    )

    if not cart_id:
        return {
            "response": (
                "No active shopping cart was found."
            ),
            "cart_changed": False,
        }

    promotion_code = state.get(
        "promotion_code"
    )

    if not promotion_code:
        return {
            "response": (
                "Please provide the promotion code."
            ),
            "cart_changed": False,
        }

    user_message = (
        state.get("user_message", "")
        .lower()
        .strip()
    )

    is_diagnosis = (
        "why" in user_message
        and (
            "not applied" in user_message
            or "wasn't applied" in user_message
            or "was not applied" in user_message
        )
    )

    # Read-only diagnosis. Do not re-apply a code merely
    # because the customer asks why it was not applied.
    if is_diagnosis:
        cart_result = get_cart.invoke(
            {
                "cart_id": cart_id,
            }
        )

        if not cart_result.get("success"):
            return {
                "response": cart_result.get(
                    "message",
                    "Unable to retrieve the current cart.",
                ),
                "cart_changed": False,
            }

        cart = cart_result.get("cart") or {}
        discount_codes = (
            cart.get("discountCodes", [])
            or []
        )

        matching_code = next(
            (
                item
                for item in discount_codes
                if (
                    str(item.get("code", "")).lower()
                    == promotion_code.lower()
                )
            ),
            None,
        )

        if matching_code is None:
            return {
                "response": (
                    f"Promotion {promotion_code} is not currently "
                    "attached to this cart. Shopify's current cart "
                    "state does not contain a rejection reason for "
                    "that code, so I cannot reliably say why an "
                    "earlier attempt failed."
                ),
                "cart_changed": False,
            }

        if matching_code.get("applicable") is False:
            return {
                "response": (
                    f"Promotion {promotion_code} was not applied "
                    "because Shopify reports that the code is not "
                    "applicable to the current cart."
                ),
                "cart_changed": False,
            }

        if matching_code.get("applicable") is True:
            return {
                "response": (
                    f"Promotion {promotion_code} is currently "
                    "applicable and attached to this cart."
                ),
                "cart_changed": False,
            }

        return {
            "response": (
                f"Promotion {promotion_code} is present on the cart, "
                "but Shopify did not provide a clear applicability "
                "status."
            ),
            "cart_changed": False,
        }

    # Mutation: apply to the current cart.
    # apply_promotion() expects argument name discount_code.
    result = apply_promotion.invoke(
        {
            "cart_id": cart_id,
            "discount_code": promotion_code,
        }
    )

    logger.info(
        "apply_promotion completed. success=%s status=%s",
        result.get("success"),
        result.get("status"),
    )

    if not result.get("success"):
        return {
            "response": result.get(
                "message",
                f"Promotion {promotion_code} could not be applied.",
            ),
            "cart_changed": False,
        }

    return {
        "response": (
            f"Promotion {promotion_code} was applied "
            "to your current cart."
        ),
        "cart_changed": True,
    }
# ============================================================
# CALCULATE CART
# ============================================================


def calculate_cart_node(
    state: CommerceState,
) -> dict:
    """
    Retrieve current Shopify cart totals.

    Shopify remains the source of truth.
    """

    logger.info(
        "Executing calculate cart node."
    )

    cart_id = state.get(
        "cart_id"
    )

    if not cart_id:
        return {
            "response": (
                "No active shopping cart was found."
            ),
            "cart_changed": False,
        }

    result = get_cart.invoke(
        {
            "cart_id": cart_id,
        }
    )

    if not result.get(
        "success"
    ):
        return {
            "response": result.get(
                "message",
                "Unable to calculate the cart total.",
            ),
            "cart_changed": False,
        }

    cart = (
        result.get(
            "cart"
        )
        or {}
    )

    cost = (
        cart.get(
            "cost"
        )
        or {}
    )

    subtotal = (
        cost.get(
            "subtotalAmount"
        )
        or {}
    )

    total = (
        cost.get(
            "totalAmount"
        )
        or {}
    )

    subtotal_amount = (
        subtotal.get(
            "amount"
        )
    )

    subtotal_currency = (
        subtotal.get(
            "currencyCode"
        )
    )

    total_amount = (
        total.get(
            "amount"
        )
    )

    total_currency = (
        total.get(
            "currencyCode"
        )
    )

    if (
        not subtotal_amount
        and not total_amount
    ):
        return {
            "response": (
                "The cart was retrieved, but Shopify "
                "did not return calculated totals."
            ),
            "cart_changed": False,
        }

    output = []

    if (
        subtotal_amount
        and subtotal_currency
    ):
        output.append(
            (
                "Your cart subtotal is "
                f"{subtotal_amount} "
                f"{subtotal_currency}."
            )
        )

    if (
        total_amount
        and total_currency
    ):
        output.append(
            (
                "Your cart total is "
                f"{total_amount} "
                f"{total_currency}."
            )
        )

    return {
        "response": " ".join(
            output
        ),
        "cart_changed": False,
    }