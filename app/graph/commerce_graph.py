# app/graph/commerce_graph.py

import logging

from langgraph.graph import (
    START,
    END,
    StateGraph,
)

from app.graph.state import CommerceState
from app.graph.router import route_intent
from app.graph.cart_router import route_cart_action

from app.graph.product_node import (
    product_node,
)

from app.graph.knowledge_node import (
    knowledge_node,
)

from app.graph.cart_nodes import (
    view_cart_node,

    extract_add_request,
    resolve_variant_node,
    add_cart_node,

    extract_update_request,
    update_cart_node,

    extract_remove_request,
    resolve_remove_line_node,
    remove_cart_node,

    extract_promotion_request,
    promotion_node,
)


logger = logging.getLogger(__name__)


# ============================================================
# ROUTING HELPERS
# ============================================================

def choose_intent(
    state: CommerceState,
) -> str:
    """
    Return the top-level intent decided by route_intent().
    """

    intent = state.get(
        "intent",
        "unknown",
    )

    logger.info(
        "Top-level intent selected: %s",
        intent,
    )

    return intent


def choose_cart_action(
    state: CommerceState,
) -> str:
    """
    Return the cart action decided by route_cart_action().
    """

    cart_action = state.get(
        "cart_action",
        "unknown",
    )

    logger.info(
        "Cart action selected: %s",
        cart_action,
    )

    return cart_action


# ============================================================
# FALLBACK NODES
# ============================================================

def unknown_intent_node(
    state: CommerceState,
) -> dict:
    """
    Fallback when the top-level router cannot determine
    which domain should handle the request.
    """

    logger.warning(
        "Unable to determine top-level commerce intent."
    )

    return {
        "response": (
            "I could not determine whether your request is "
            "about products, commerce knowledge, or your cart."
        ),
        "cart_changed": False,
    }


def unknown_cart_action_node(
    state: CommerceState,
) -> dict:
    """
    Fallback when the request is recognized as cart-related
    but the exact cart action cannot be determined.
    """

    logger.warning(
        "Unable to determine cart action."
    )

    return {
        "response": (
            "I understood that your request is related to your "
            "cart, but I could not determine the cart operation."
        ),
        "cart_changed": False,
    }


# ============================================================
# ERROR ROUTING HELPERS
# ============================================================

def route_after_add_extraction(
    state: CommerceState,
) -> str:
    """
    Stop the add workflow if extraction failed.
    """

    if state.get("error"):
        return "error"

    return "continue"


def route_after_variant_resolution(
    state: CommerceState,
) -> str:
    """
    Stop the add workflow if variant resolution failed.
    """

    if state.get("error"):
        return "error"

    return "continue"


def route_after_update_extraction(
    state: CommerceState,
) -> str:
    """
    Stop the update workflow if extraction failed.
    """

    if state.get("error"):
        return "error"

    return "continue"


def route_after_remove_extraction(
    state: CommerceState,
) -> str:
    """
    Stop remove workflow if extraction failed.
    """

    if state.get("error"):
        return "error"

    return "continue"


def route_after_remove_resolution(
    state: CommerceState,
) -> str:
    """
    Stop remove workflow if cart-line resolution failed.

    Note:
    Some resolution failures may already populate response
    instead of error, so check both.
    """

    if state.get("error"):
        return "error"

    if state.get("response"):
        return "stop"

    return "continue"


def route_after_promotion_extraction(
    state: CommerceState,
) -> str:
    """
    Stop promotion workflow if promotion-code extraction failed.
    """

    if state.get("error"):
        return "error"

    return "continue"


def graph_error_node(
    state: CommerceState,
) -> dict:
    """
    Convert internal graph errors into the final response.
    """

    error = state.get(
        "error"
    )

    logger.warning(
        "Commerce graph workflow error: %s",
        error,
    )

    return {
        "response": (
            error
            or "Unable to process the commerce request."
        ),
        "cart_changed": False,
    }


# ============================================================
# BUILD GRAPH
# ============================================================

builder = StateGraph(
    CommerceState
)


# ------------------------------------------------------------
# TOP-LEVEL NODES
# ------------------------------------------------------------

builder.add_node(
    "router",
    route_intent,
)

builder.add_node(
    "product",
    product_node,
)

builder.add_node(
    "knowledge",
    knowledge_node,
)

builder.add_node(
    "cart_router",
    route_cart_action,
)

builder.add_node(
    "unknown_intent",
    unknown_intent_node,
)

builder.add_node(
    "unknown_cart_action",
    unknown_cart_action_node,
)

builder.add_node(
    "graph_error",
    graph_error_node,
)


# ------------------------------------------------------------
# VIEW CART
# ------------------------------------------------------------

builder.add_node(
    "cart_view",
    view_cart_node,
)


# ------------------------------------------------------------
# ADD TO CART
# ------------------------------------------------------------

builder.add_node(
    "extract_add",
    extract_add_request,
)

builder.add_node(
    "resolve_variant",
    resolve_variant_node,
)

builder.add_node(
    "cart_add",
    add_cart_node,
)


# ------------------------------------------------------------
# UPDATE QUANTITY
# ------------------------------------------------------------

builder.add_node(
    "extract_update",
    extract_update_request,
)

builder.add_node(
    "cart_update",
    update_cart_node,
)


# ------------------------------------------------------------
# REMOVE FROM CART
# ------------------------------------------------------------

builder.add_node(
    "extract_remove",
    extract_remove_request,
)

builder.add_node(
    "resolve_remove_line",
    resolve_remove_line_node,
)

builder.add_node(
    "cart_remove",
    remove_cart_node,
)


# ------------------------------------------------------------
# PROMOTION
# ------------------------------------------------------------

builder.add_node(
    "extract_promotion",
    extract_promotion_request,
)

builder.add_node(
    "cart_promotion",
    promotion_node,
)


# ============================================================
# GRAPH ENTRY
# ============================================================

builder.add_edge(
    START,
    "router",
)


# ============================================================
# TOP-LEVEL ROUTING
# ============================================================

builder.add_conditional_edges(
    "router",
    choose_intent,
    {
        "product": "product",
        "knowledge": "knowledge",
        "cart": "cart_router",
        "unknown": "unknown_intent",
    },
)


# ============================================================
# CART ACTION ROUTING
# ============================================================

builder.add_conditional_edges(
    "cart_router",
    choose_cart_action,
    {
        "view": "cart_view",
        "add": "extract_add",
        "update": "extract_update",
        "remove": "extract_remove",
        "promotion": "extract_promotion",
        "unknown": "unknown_cart_action",
    },
)


# ============================================================
# ADD TO CART WORKFLOW
# ============================================================

builder.add_conditional_edges(
    "extract_add",
    route_after_add_extraction,
    {
        "continue": "resolve_variant",
        "error": "graph_error",
    },
)

builder.add_conditional_edges(
    "resolve_variant",
    route_after_variant_resolution,
    {
        "continue": "cart_add",
        "error": "graph_error",
    },
)


# ============================================================
# UPDATE QUANTITY WORKFLOW
# ============================================================

builder.add_conditional_edges(
    "extract_update",
    route_after_update_extraction,
    {
        "continue": "cart_update",
        "error": "graph_error",
    },
)


# ============================================================
# REMOVE FROM CART WORKFLOW
# ============================================================

builder.add_conditional_edges(
    "extract_remove",
    route_after_remove_extraction,
    {
        "continue": "resolve_remove_line",
        "error": "graph_error",
    },
)

builder.add_conditional_edges(
    "resolve_remove_line",
    route_after_remove_resolution,
    {
        "continue": "cart_remove",
        "error": "graph_error",
        "stop": END,
    },
)


# ============================================================
# PROMOTION WORKFLOW
# ============================================================

builder.add_conditional_edges(
    "extract_promotion",
    route_after_promotion_extraction,
    {
        "continue": "cart_promotion",
        "error": "graph_error",
    },
)


# ============================================================
# TERMINAL EDGES
# ============================================================

builder.add_edge(
    "product",
    END,
)

builder.add_edge(
    "knowledge",
    END,
)

builder.add_edge(
    "cart_view",
    END,
)

builder.add_edge(
    "cart_add",
    END,
)

builder.add_edge(
    "cart_update",
    END,
)

builder.add_edge(
    "cart_remove",
    END,
)

builder.add_edge(
    "cart_promotion",
    END,
)

builder.add_edge(
    "unknown_intent",
    END,
)

builder.add_edge(
    "unknown_cart_action",
    END,
)

builder.add_edge(
    "graph_error",
    END,
)


# ============================================================
# COMPILE GRAPH
# ============================================================

commerce_graph = builder.compile()