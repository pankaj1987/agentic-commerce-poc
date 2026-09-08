import logging

from app.agents.order_agent import order_agent
from app.graph.state import CommerceState
from app.utils.message_utils import extract_message_text


logger = logging.getLogger(__name__)


def order_node(state: CommerceState) -> dict:
    logger.info("Executing Order node.")

    result = order_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": state["user_message"],
                }
            ]
        }
    )

    messages = result.get("messages", [])
    if not messages:
        return {
            "error": "Order Agent returned no response.",
            "cart_changed": False,
        }

    response = extract_message_text(messages[-1])
    return {
        "response": response,
        "intent": "order",
        "cart_changed": False,
    }
