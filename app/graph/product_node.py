# app/graph/product_node.py

import logging

from app.agents.product_agent import product_agent
from app.graph.state import CommerceState
from app.utils.message_utils import extract_message_text


logger = logging.getLogger(__name__)


def product_node(
    state: CommerceState,
) -> dict:

    logger.info(
        "Executing Product node."
    )

    result = product_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": state["user_message"],
                }
            ]
        }
    )

    messages = result.get(
        "messages",
        [],
    )

    if not messages:
        return {
            "error": (
                "Product Agent returned no response."
            )
        }

    response = extract_message_text(
        messages[-1]
    )

    return {
        "response": response,
        "cart_changed": False,
    }