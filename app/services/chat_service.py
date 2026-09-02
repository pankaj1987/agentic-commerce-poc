import logging
import re
from typing import Any

from fastapi.concurrency import run_in_threadpool

from app.agents.cart_agent import cart_agent
from app.agents.product_agent import product_agent

logger = logging.getLogger(__name__)


class ChatService:
    # ============================================================
    # PROCESS MESSAGE
    # ============================================================

    @staticmethod
    async def process_message(
        message: str,
        cart_id: str | None = None,
    ) -> dict[str, Any]:
        logger.info(
            "Processing chat message=%r cart_id_present=%s",
            message,
            bool(cart_id),
        )

        # --------------------------------------------------------
        # Determine which agent should handle the request
        # --------------------------------------------------------
        is_cart_request = ChatService._is_cart_request(message)

        if is_cart_request:
            logger.info("Routing request to Cart Agent.")
            agent_message = message

            if cart_id:
                agent_message = (
                    f"{message}\n\n"
                    "CURRENT SHOPIFY CART CONTEXT:\n"
                    f"cart_id={cart_id}\n\n"
                    "Use this cart ID for all cart operations. "
                    "Do not ask the customer for another cart ID."
                )

                logger.info(
                    "Invoking Cart Agent with cart context present=%s",
                    bool(cart_id),
                )

            result = await run_in_threadpool(
                cart_agent.invoke,
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": agent_message,
                        }
                    ]
                },
            )
        else:
            logger.info("Routing request to Product Agent.")
            result = await run_in_threadpool(
                product_agent.invoke,
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": message,
                        }
                    ]
                },
            )

        logger.info("Agent execution completed.")

        # --------------------------------------------------------
        # Extract final agent message
        # --------------------------------------------------------
        messages = result.get("messages", [])
        if not messages:
            raise RuntimeError("Agent returned no messages.")

        final_message = messages[-1]

        # --------------------------------------------------------
        # Normalize formats into a plain string.
        # --------------------------------------------------------
        response_content = ChatService._extract_message_text(final_message)

        logger.info("Final message type: %s", type(final_message).__name__)
        logger.info("Final message content: %r", final_message.content)
        logger.info(
            "Final message additional_kwargs: %r",
            getattr(final_message, "additional_kwargs", None),
        )
        logger.info(
            "Final message response_metadata: %r",
            getattr(final_message, "response_metadata", None),
        )

        if not response_content:
            raise RuntimeError("Agent returned an empty final response.")

        logger.info("Final agent response extracted successfully.")

        return {
            "success": True,
            "response": response_content,
            "cart_id": cart_id,
        }

    # ============================================================
    # AGENT ROUTING
    # ============================================================

    @staticmethod
    def _is_cart_request(message: str) -> bool:
        if not message:
            return False

        text = message.lower().strip()

        # Explicit cart references
        if "cart" in text:
            return True

        # Quantity modification
        quantity_patterns = [
            r"\b(change|update|set|increase|decrease)\b.*\b(quantity|qty)\b",
            r"\b(quantity|qty)\b.*\b(change|update|set|increase|decrease)\b",
            r"\b(change|update|set)\b.*\bline\b",
            r"\bline\s+\d+\b.*\b(quantity|qty)\b",
            r"\b(make)\b.*\b(quantity|qty)\b",
        ]
        if any(re.search(pattern, text) for pattern in quantity_patterns):
            return True

        # Remove/delete item
        remove_patterns = [
            r"\b(remove|delete)\b.*\b(item|product|shoe|line)\b",
            r"\btake\b.*\bout\b",
        ]
        if any(re.search(pattern, text) for pattern in remove_patterns):
            return True

        # Promotion / coupon / discount
        promotion_keywords = [
            "promotion",
            "promo code",
            "discount code",
            "coupon",
            "apply code",
        ]
        if any(keyword in text for keyword in promotion_keywords):
            return True

        return False

    # ============================================================
    # NORMALIZE LLM RESPONSE
    # ============================================================

    @staticmethod
    def _extract_message_text(message: Any) -> str:
        # 1. Standard content extraction
        content = getattr(message, "content", None)
        extracted = ChatService._extract_text_content(content)

        if extracted:
            return extracted

        # 2. Some LangChain model integrations expose normalized text separately
        text_value = getattr(message, "text", None)
        if callable(text_value):
            try:
                text_value = text_value()
            except Exception:
                text_value = None

        if isinstance(text_value, str):
            return text_value.strip()

        return ""

    @staticmethod
    def _extract_text_content(content: Any) -> str:
        # String response
        if isinstance(content, str):
            return content.strip()

        # Structured list of content blocks
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    block_text = block.get("text")
                    if block_text:
                        text_parts.append(str(block_text))
                elif isinstance(block, str):
                    text_parts.append(block)

            return "\n".join(text_parts).strip()

        # Defensive fallback
        if content is None:
            return ""

        return str(content).strip()