# app/graph/cart_router.py

import re

from app.graph.state import CommerceState


def route_cart_action(
    state: CommerceState,
) -> dict:

    text = (
        state["user_message"]
        .lower()
        .strip()
    )

    # --------------------------------------------
    # VIEW
    # --------------------------------------------

    view_patterns = [
        r"\bshow\b.*\bcart\b",
        r"\bview\b.*\bcart\b",
        r"\bwhat.*\bcart\b",
        r"\bdisplay\b.*\bcart\b",
        r"\bcheck\b.*\bcart\b",
    ]

    if any(
        re.search(pattern, text)
        for pattern in view_patterns
    ):
        return {
            "cart_action": "view"
        }

    # --------------------------------------------
    # UPDATE
    # --------------------------------------------

    update_patterns = [
        r"\bchange\b.*\bquantity\b",
        r"\bupdate\b.*\bquantity\b",
        r"\bset\b.*\bquantity\b",
        r"\bline\s+\d+\b.*\bto\b",
    ]

    if any(
        re.search(pattern, text)
        for pattern in update_patterns
    ):
        return {
            "cart_action": "update"
        }

    # --------------------------------------------
    # REMOVE
    # --------------------------------------------

    if re.search(
        r"\b(remove|delete)\b",
        text,
    ):
        return {
            "cart_action": "remove"
        }

    # --------------------------------------------
    # PROMOTION
    # --------------------------------------------

    promotion_patterns = [
        r"\bpromo\b",
        r"\bpromotion\b",
        r"\bdiscount code\b",
        r"\bcoupon\b",
        r"\b(apply|use)\b\s+[a-z0-9][a-z0-9_-]{3,}\b",
        r"\bwhy\b.*\bnot applied\b",
        r"\bwhy\b.*\bwasn't applied\b",
        r"\bwhy\b.*\bwas not applied\b",
    ]

    if any(
        re.search(pattern, text)
        for pattern in promotion_patterns
    ):
        return {
            "cart_action": "promotion"
        }

    # --------------------------------------------
    # TOTAL
    # --------------------------------------------

    total_patterns = [
        r"\bcart total\b",
        r"\bsubtotal\b",
        r"\bhow much.*cart\b",
        r"\bwhat will i pay\b",
    ]

    if any(
        re.search(pattern, text)
        for pattern in total_patterns
    ):
        return {
            "cart_action": "calculate"
        }

    # --------------------------------------------
    # ADD
    # --------------------------------------------

    if re.search(
        r"\badd\b",
        text,
    ):
        return {
            "cart_action": "add"
        }

    return {
        "cart_action": "unknown"
    }