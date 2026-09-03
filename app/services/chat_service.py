import logging
from typing import Any

from fastapi.concurrency import run_in_threadpool

from app.graph.commerce_graph import commerce_graph


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
        """
        Process the user request through LangGraph.

        ChatService no longer performs agent routing directly.
        Product, knowledge and cart routing is handled by
        commerce_graph.
        """

        logger.info(
            "Processing chat message=%r cart_id_present=%s",
            message,
            bool(cart_id),
        )

        if not message or not message.strip():
            raise ValueError(
                "Chat message cannot be empty."
            )

        # --------------------------------------------------------
        # INITIAL LANGGRAPH STATE
        # --------------------------------------------------------

        initial_state = {
            "user_message": message.strip(),
            "cart_id": cart_id,
            "intent": "unknown",
            "cart_action": "unknown",
            "cart_changed": False,
            "error": None,
        }

        logger.info(
            "Invoking CommerceGraph."
        )

        try:
            result = await run_in_threadpool(
                commerce_graph.invoke,
                initial_state,
            )

        except Exception:
            logger.exception(
                "CommerceGraph execution failed."
            )

            raise RuntimeError(
                "Unable to process the commerce request."
            )

        logger.info(
            "CommerceGraph execution completed."
        )

        # --------------------------------------------------------
        # EXTRACT GRAPH RESPONSE
        # --------------------------------------------------------

        if not result:
            raise RuntimeError(
                "CommerceGraph returned no result."
            )

        response_content = result.get(
            "response"
        )

        error = result.get(
            "error"
        )

        cart_changed = result.get(
            "cart_changed",
            False,
        )

        # --------------------------------------------------------
        # HANDLE GRAPH ERROR
        # --------------------------------------------------------

        if not response_content:
            if error:
                logger.warning(
                    "CommerceGraph returned error: %s",
                    error,
                )

                raise RuntimeError(
                    str(error)
                )

            raise RuntimeError(
                "CommerceGraph returned an empty response."
            )

        # --------------------------------------------------------
        # NORMALIZE RESPONSE
        # --------------------------------------------------------

        response_content = (
            ChatService._normalize_response(
                response_content
            )
        )

        if not response_content:
            raise RuntimeError(
                "CommerceGraph returned an empty response."
            )

        logger.info(
            (
                "CommerceGraph response completed. "
                "intent=%s cart_action=%s "
                "cart_changed=%s"
            ),
            result.get("intent"),
            result.get("cart_action"),
            cart_changed,
        )

        # --------------------------------------------------------
        # RETURN API RESPONSE
        # --------------------------------------------------------

        return {
            "success": True,
            "response": response_content,
            "cart_id": result.get(
                "cart_id",
                cart_id,
            ),
            "cart_changed": cart_changed,
        }

    # ============================================================
    # NORMALIZE GRAPH RESPONSE
    # ============================================================

    @staticmethod
    def _normalize_response(
        response: Any,
    ) -> str:
        """
        Normalize graph response into a plain string.

        Most LangGraph nodes should already return strings,
        but this keeps ChatService defensive against structured
        LLM responses returned by Product or Knowledge nodes.
        """

        # Standard string
        if isinstance(
            response,
            str,
        ):
            return response.strip()

        # Structured content-block list
        if isinstance(
            response,
            list,
        ):
            text_parts = []

            for block in response:
                if isinstance(
                    block,
                    str,
                ):
                    text_parts.append(
                        block
                    )

                elif isinstance(
                    block,
                    dict,
                ):
                    block_text = block.get(
                        "text"
                    )

                    if block_text:
                        text_parts.append(
                            str(block_text)
                        )

            return "\n".join(
                text_parts
            ).strip()

        # Defensive fallback
        if response is None:
            return ""

        return str(
            response
        ).strip()