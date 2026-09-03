# app/services/chat_service.py

import logging
from typing import Any

from fastapi.concurrency import run_in_threadpool

from app.graph.commerce_graph import (
    commerce_graph,
)


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
        Process a customer request through the LangGraph commerce
        orchestration layer.

        The CommerceGraph is responsible for:

        - multi-intent planning
        - product-domain execution
        - knowledge/RAG execution
        - cart workflow execution
        - response aggregation
        """

        logger.info(
            (
                "Processing chat message=%r "
                "cart_id_present=%s"
            ),
            message,
            bool(cart_id),
        )

        # ========================================================
        # INPUT VALIDATION
        # ========================================================

        if (
            not message
            or not message.strip()
        ):
            raise ValueError(
                "Chat message cannot be empty."
            )

        normalized_message = (
            message.strip()
        )

        # ========================================================
        # INITIAL LANGGRAPH STATE
        # ========================================================

        initial_state = {
            "user_message": (
                normalized_message
            ),
            "cart_id": cart_id,

            # Domain state
            "intent": "unknown",
            "cart_action": "unknown",

            # Multi-intent orchestration state
            "tasks": [],
            "task_results": [],

            # Mutation/error state
            "cart_changed": False,
            "error": None,
        }

        logger.info(
            "Invoking CommerceGraph."
        )

        # ========================================================
        # EXECUTE LANGGRAPH
        # ========================================================

        try:

            result = await run_in_threadpool(
                commerce_graph.invoke,
                initial_state,
            )

        except Exception as exc:

            logger.exception(
                "CommerceGraph execution failed."
            )

            raise RuntimeError(
                "Unable to process the commerce request."
            ) from exc

        logger.info(
            "CommerceGraph execution completed."
        )

        # ========================================================
        # VALIDATE GRAPH RESULT
        # ========================================================

        if not result:

            raise RuntimeError(
                "CommerceGraph returned no result."
            )

        response_content = (
            result.get(
                "response"
            )
        )

        error = (
            result.get(
                "error"
            )
        )

        cart_changed = bool(
            result.get(
                "cart_changed",
                False,
            )
        )

        # ========================================================
        # HANDLE GRAPH ERROR
        # ========================================================

        if not response_content:

            if error:

                logger.warning(
                    (
                        "CommerceGraph returned "
                        "error: %s"
                    ),
                    error,
                )

                raise RuntimeError(
                    str(error)
                )

            raise RuntimeError(
                "CommerceGraph returned an empty response."
            )

        # ========================================================
        # NORMALIZE RESPONSE
        # ========================================================

        response_content = (
            ChatService._normalize_response(
                response_content
            )
        )

        if not response_content:

            raise RuntimeError(
                "CommerceGraph returned an empty response."
            )

        # ========================================================
        # OBSERVABILITY
        # ========================================================

        task_results = result.get(
            "task_results",
            [],
        )

        logger.info(
            (
                "CommerceGraph response completed. "
                "intent=%s "
                "cart_action=%s "
                "cart_changed=%s "
                "task_count=%s"
            ),
            result.get(
                "intent"
            ),
            result.get(
                "cart_action"
            ),
            cart_changed,
            len(task_results),
        )

        # ========================================================
        # RETURN API RESPONSE
        # ========================================================

        return {
            "success": True,
            "response": (
                response_content
            ),
            "cart_id": result.get(
                "cart_id",
                cart_id,
            ),
            "cart_changed": (
                cart_changed
            ),
        }

    # ============================================================
    # NORMALIZE GRAPH RESPONSE
    # ============================================================

    @staticmethod
    def _normalize_response(
        response: Any,
    ) -> str:
        """
        Normalize LangGraph/LLM output into a plain string.

        Most commerce graph nodes already return strings, but this
        method keeps the API layer defensive against providers that
        return structured message content blocks.
        """

        # --------------------------------------------------------
        # STANDARD STRING
        # --------------------------------------------------------

        if isinstance(
            response,
            str,
        ):
            return (
                response.strip()
            )

        # --------------------------------------------------------
        # STRUCTURED CONTENT-BLOCK LIST
        # --------------------------------------------------------

        if isinstance(
            response,
            list,
        ):

            text_parts: list[str] = []

            for block in response:

                if isinstance(
                    block,
                    str,
                ):

                    text_parts.append(
                        block
                    )

                    continue

                if isinstance(
                    block,
                    dict,
                ):

                    block_text = (
                        block.get(
                            "text"
                        )
                    )

                    if block_text:

                        text_parts.append(
                            str(
                                block_text
                            )
                        )

            return (
                "\n".join(
                    text_parts
                )
                .strip()
            )

        # --------------------------------------------------------
        # NONE
        # --------------------------------------------------------

        if response is None:
            return ""

        # --------------------------------------------------------
        # DEFENSIVE FALLBACK
        # --------------------------------------------------------

        return (
            str(
                response
            )
            .strip()
        )