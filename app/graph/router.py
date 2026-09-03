# app/graph/router.py

import re

from app.graph.state import CommerceState


def route_intent(
    state: CommerceState,
) -> dict:

    text = (
        state["user_message"]
        .lower()
        .strip()
    )

    # --------------------------------------------
    # CART
    # --------------------------------------------

    cart_patterns = [
        r"\bcart\b",
        r"\badd\b.*\bcart\b",
        r"\bremove\b",
        r"\bdelete\b.*\bitem\b",
        r"\bchange\b.*\bquantity\b",
        r"\bupdate\b.*\bquantity\b",
        r"\bquantity\b.*\bto\b",
        r"\bline\s+\d+\b",
        r"\bpromo code\b",
        r"\bdiscount code\b",
        r"\bcoupon\b",
        r"\bapply\b.*\bpromotion\b",
        r"\b(apply|use)\b\s+[a-z0-9][a-z0-9_-]{3,}\b",
        r"\bwhy\b.*\bnot applied\b",
        r"\bwhy\b.*\bwasn't applied\b",
        r"\bwhy\b.*\bwas not applied\b",
        r"\bsubtotal\b",
        r"\bcart total\b",
    ]

    if any(
        re.search(pattern, text)
        for pattern in cart_patterns
    ):
        return {
            "intent": "cart"
        }

    # --------------------------------------------
    # KNOWLEDGE / RAG
    # --------------------------------------------

    knowledge_patterns = [
    r"\breturn policy\b",
    r"\brefund policy\b",
    r"\bshipping policy\b",
    r"\bdelivery policy\b",

    # Promotion / policy knowledge
    r"\bpromotion rules?\b",
    r"\bpromo rules?\b",
    r"\bdiscount rules?\b",
    r"\bcoupon rules?\b",

    # Generic policy/rule questions such as:
    # "What are SAVE20 rules?"
    # "What are the eligibility conditions for SAVE20?"
    r"\brules?\b",
    r"\beligibility\b",
    r"\bterms(?: and conditions)?\b",
    r"\bconditions\b",

    r"\border.*split\b",
    r"\bbenefits of\b",
    r"\bproduct benefits\b",
]

    if any(
        re.search(pattern, text)
        for pattern in knowledge_patterns
    ):
        return {
            "intent": "knowledge"
        }

    # --------------------------------------------
    # PRODUCT
    # --------------------------------------------

    return {
        "intent": "product"
    }