# app/services/chat_service.py

import logging
from typing import Any

from fastapi.concurrency import (
    run_in_threadpool,
)
from langchain_core.messages import (
    HumanMessage,
)

from app.graph.commerce_graph import (
    commerce_graph,
)
from app.persistence.repositories.session_repository import (
    SessionRepository,
)
from app.services.session_service import (
    SessionService,
)


logger = logging.getLogger(__name__)


class ChatService:

    # ============================================================
    # PROCESS MESSAGE
    # ============================================================

    @staticmethod
    async def process_message(
        message: str,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Process one customer conversation turn.

        Public client state:
            session_id

        Server-side state:
            thread_id
            cart_id

        Lifecycle:

        1. Resolve/create CommerceSession.
        2. Obtain thread_id from CommerceSession.
        3. Obtain Shopify cart_id from CommerceSession.
        4. Add current HumanMessage.
        5. Invoke LangGraph using thread_id.
        6. LangGraph loads previous conversation checkpoint.
        7. Execute commerce workflow.
        8. Persist changed cart_id if graph created/replaced cart.
        9. Return session_id only.

        cart_id and thread_id never leave the backend.
        """

        normalized_message = (
            message.strip()
            if message
            else ""
        )

        if not normalized_message:
            raise ValueError(
                "Chat message cannot be empty."
            )

        # ========================================================
        # STEP 1
        # RESOLVE OR CREATE COMMERCE SESSION
        # ========================================================

        try:
            commerce_session = (
                await run_in_threadpool(
                    SessionService.get_or_create_session,
                    session_id,
                    user_id,
                )
            )

        except (
            ValueError,
            PermissionError,
        ):
            raise

        except Exception:
            logger.exception(
                "Unable to resolve commerce session."
            )

            raise RuntimeError(
                "Unable to initialize the commerce session."
            )

        logger.info(
            (
                "Processing commerce conversation. "
                "session_present=%s "
                "thread_present=%s "
                "cart_present=%s"
            ),
            bool(
                commerce_session.session_id
            ),
            bool(
                commerce_session.thread_id
            ),
            bool(
                commerce_session.cart_id
            ),
        )

        # ========================================================
        # STEP 2
        # CREATE CURRENT LANGGRAPH INPUT
        # ========================================================
        #
        # Do NOT manually load previous messages here.
        #
        # PostgresSaver will load the existing state using
        # thread_id.
        #
        # add_messages then merges this HumanMessage with the
        # persisted messages channel.
        #

        initial_state = {
            "user_message": (
                normalized_message
            ),

            "messages": [
                HumanMessage(
                    content=normalized_message
                )
            ],

            # Shopify cart is server-owned.
            #
            # It may legitimately be None for a new session.
            "cart_id": (
                commerce_session.cart_id
            ),

            # Reset transient per-turn state.
            "intent": "unknown",
            "cart_action": "unknown",

            "tasks": [],
            "task_results": [],

            "cart_changed": False,

            "error": None,
        }

        # ========================================================
        # STEP 3
        # LANGGRAPH THREAD CONFIGURATION
        # ========================================================

        config = {
            "configurable": {
                "thread_id": (
                    commerce_session.thread_id
                )
            }
        }

        logger.info(
            "Invoking persistent CommerceGraph."
        )

        # ========================================================
        # STEP 4
        # INVOKE GRAPH
        # ========================================================

        try:
            result = await run_in_threadpool(
                commerce_graph.invoke,
                initial_state,
                config,
            )

        except Exception:
            logger.exception(
                "CommerceGraph execution failed."
            )

            raise RuntimeError(
                "Unable to process the commerce request."
            )

        if not result:
            raise RuntimeError(
                "CommerceGraph returned no result."
            )

        # ========================================================
        # STEP 5
        # EXTRACT GRAPH RESPONSE
        # ========================================================

        response_content = result.get(
            "response"
        )

        error = result.get(
            "error"
        )

        cart_changed = bool(
            result.get(
                "cart_changed",
                False,
            )
        )

        if not response_content:

            if error:
                logger.warning(
                    "CommerceGraph returned an error."
                )

                raise RuntimeError(
                    str(error)
                )

            raise RuntimeError(
                "CommerceGraph returned an empty response."
            )

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
        # STEP 6
        # SYNCHRONIZE CART ASSOCIATION
        # ========================================================
        #
        # The graph may:
        #
        # - reuse existing cart
        # - create a new cart
        # - replace an invalid cart
        #
        # If the graph returns a different cart_id, persist it
        # against the application session.
        #

        result_cart_id = result.get(
            "cart_id"
        )

        if (
            result_cart_id
            and result_cart_id
            != commerce_session.cart_id
        ):

            logger.info(
                (
                    "CommerceGraph returned a new cart "
                    "association. Persisting it."
                )
            )

            try:
                commerce_session = (
                    await run_in_threadpool(
                        SessionRepository.update_cart_id,
                        commerce_session.session_id,
                        result_cart_id,
                    )
                )

            except Exception:
                logger.exception(
                    (
                        "Unable to persist cart/session "
                        "association."
                    )
                )

                raise RuntimeError(
                    (
                        "The commerce operation completed, "
                        "but its session state could not "
                        "be persisted."
                    )
                )

        else:

            # Update session activity metadata.
            #
            # Failure to update last_activity_at should not
            # fail an otherwise successful commerce request.

            try:
                await run_in_threadpool(
                    SessionRepository.touch_session,
                    commerce_session.session_id,
                )

            except Exception:
                logger.exception(
                    (
                        "Unable to update commerce "
                        "session activity time."
                    )
                )

        # ========================================================
        # STEP 7
        # LOG SAFE EXECUTION METADATA
        # ========================================================

        logger.info(
            (
                "Commerce conversation completed. "
                "intent=%s "
                "cart_action=%s "
                "cart_changed=%s "
                "cart_present=%s"
            ),
            result.get(
                "intent"
            ),
            result.get(
                "cart_action"
            ),
            cart_changed,
            bool(
                result_cart_id
                or commerce_session.cart_id
            ),
        )

        # ========================================================
        # STEP 8
        # PUBLIC RESPONSE
        # ========================================================
        #
        # Do NOT return:
        #
        # cart_id
        # thread_id
        #

        return {
            "success": True,

            "response": (
                response_content
            ),

            "session_id": (
                commerce_session.session_id
            ),

            "cart_changed": (
                cart_changed
            ),
        }

    # ============================================================
    # NORMALIZE RESPONSE
    # ============================================================

    @staticmethod
    def _normalize_response(
        response: Any,
    ) -> str:

        if isinstance(
            response,
            str,
        ):
            return response.strip()

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

                elif isinstance(
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

            return "\n".join(
                text_parts
            ).strip()

        if response is None:
            return ""

        return str(
            response
        ).strip()