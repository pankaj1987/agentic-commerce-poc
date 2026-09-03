# app/graph/commerce_graph.py

import logging
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from app.graph.cart_nodes import (
    add_cart_node,
    calculate_cart_node,
    extract_add_request,
    extract_promotion_request,
    extract_remove_request,
    extract_update_request,
    promotion_node,
    remove_cart_node,
    resolve_remove_line_node,
    resolve_variant_node,
    update_cart_node,
    view_cart_node,
)

from app.graph.conditional_nodes import (
    conditional_add_cart_node,
    conditional_inventory_check_node,
    conditional_inventory_unavailable_node,
    extract_conditional_inventory_request,
    resolve_conditional_variant_node,
    route_after_inventory_check,
)

from app.graph.cart_router import route_cart_action
from app.graph.knowledge_node import knowledge_node
from app.graph.planner import plan_tasks_node
from app.graph.product_node import product_node
from app.graph.router import route_intent
from app.graph.state import CommerceState
from app.persistence.checkpointer import get_checkpointer


logger = logging.getLogger(__name__)


# ============================================================
# DOMAIN ENTRY
# ============================================================


def domain_entry_node(
    state: CommerceState,
) -> dict[str, Any]:
    """
    Determine the domain for a single planned task.

    If the multi-intent planner has already supplied a valid
    domain, preserve it.

    Otherwise fall back to the existing deterministic router.

    This allows:
    - planner-driven multi-intent execution
    - backward-compatible single-domain routing
    """

    planned_intent = state.get(
        "intent",
        "unknown",
    )

    if planned_intent in {
        "product",
        "knowledge",
        "cart",
        "conditional",
    }:
        logger.info(
            "Using planner-selected domain intent: %s",
            planned_intent,
        )

        return {
            "intent": planned_intent
        }

    logger.info(
        "No valid planned intent supplied. "
        "Falling back to deterministic router."
    )

    return route_intent(state)


# ============================================================
# ROUTING HELPERS
# ============================================================


def choose_intent(
    state: CommerceState,
) -> str:
    """
    Return the top-level domain selected for the current task.
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
    Return the cart action selected by the deterministic
    cart router.
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
) -> dict[str, Any]:
    """
    Fallback when the target commerce domain cannot be
    determined.
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
) -> dict[str, Any]:
    """
    Fallback when a request is cart-related but the exact cart
    operation cannot be determined.
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

    if state.get("error"):
        return "error"

    return "continue"


def route_after_variant_resolution(
    state: CommerceState,
) -> str:

    if state.get("error"):
        return "error"

    return "continue"


def route_after_update_extraction(
    state: CommerceState,
) -> str:

    if state.get("error"):
        return "error"

    return "continue"


def route_after_remove_extraction(
    state: CommerceState,
) -> str:

    if state.get("error"):
        return "error"

    return "continue"


def route_after_remove_resolution(
    state: CommerceState,
) -> str:

    if state.get("error"):
        return "error"

    if state.get("response"):
        return "stop"

    return "continue"


def route_after_promotion_extraction(
    state: CommerceState,
) -> str:

    if state.get("error"):
        return "error"

    return "continue"


def graph_error_node(
    state: CommerceState,
) -> dict[str, Any]:
    """
    Convert internal workflow errors into a customer-facing
    graph response.
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
# BUILD SINGLE-DOMAIN GRAPH
# ============================================================

domain_builder = StateGraph(
    CommerceState
)


# ============================================================
# DOMAIN NODES
# ============================================================

domain_builder.add_node(
    "domain_entry",
    domain_entry_node,
)

domain_builder.add_node(
    "product",
    product_node,
)

domain_builder.add_node(
    "knowledge",
    knowledge_node,
)

domain_builder.add_node(
    "cart_router",
    route_cart_action,
)

domain_builder.add_node(
    "unknown_intent",
    unknown_intent_node,
)

domain_builder.add_node(
    "unknown_cart_action",
    unknown_cart_action_node,
)

domain_builder.add_node(
    "graph_error",
    graph_error_node,
)

domain_builder.add_node(
    "cart_calculate",
    calculate_cart_node,
)


domain_builder.add_node(
    "conditional_extract",
    extract_conditional_inventory_request,
)

domain_builder.add_node(
    "conditional_resolve",
    resolve_conditional_variant_node,
)

domain_builder.add_node(
    "conditional_inventory_check",
    conditional_inventory_check_node,
)

domain_builder.add_node(
    "conditional_add",
    conditional_add_cart_node,
)

domain_builder.add_node(
    "conditional_unavailable",
    conditional_inventory_unavailable_node,
)


# ============================================================
# CART VIEW
# ============================================================

domain_builder.add_node(
    "cart_view",
    view_cart_node,
)


# ============================================================
# ADD TO CART
# ============================================================

domain_builder.add_node(
    "extract_add",
    extract_add_request,
)

domain_builder.add_node(
    "resolve_variant",
    resolve_variant_node,
)

domain_builder.add_node(
    "cart_add",
    add_cart_node,
)


# ============================================================
# UPDATE CART
# ============================================================

domain_builder.add_node(
    "extract_update",
    extract_update_request,
)

domain_builder.add_node(
    "cart_update",
    update_cart_node,
)


# ============================================================
# REMOVE FROM CART
# ============================================================

domain_builder.add_node(
    "extract_remove",
    extract_remove_request,
)

domain_builder.add_node(
    "resolve_remove_line",
    resolve_remove_line_node,
)

domain_builder.add_node(
    "cart_remove",
    remove_cart_node,
)


# ============================================================
# PROMOTION
# ============================================================

domain_builder.add_node(
    "extract_promotion",
    extract_promotion_request,
)

domain_builder.add_node(
    "cart_promotion",
    promotion_node,
)


# ============================================================
# DOMAIN GRAPH ENTRY
# ============================================================

domain_builder.add_edge(
    START,
    "domain_entry",
)


# ============================================================
# DOMAIN ROUTING
# ============================================================

domain_builder.add_conditional_edges(
    "domain_entry",
    choose_intent,
    {
        "product": "product",
        "knowledge": "knowledge",
        "cart": "cart_router",
        "conditional": "conditional_extract",
        "unknown": "unknown_intent",
    },
)


# ============================================================
# CART ACTION ROUTING
# ============================================================

domain_builder.add_conditional_edges(
    "cart_router",
    choose_cart_action,
    {
        "view": "cart_view",
        "add": "extract_add",
        "update": "extract_update",
        "remove": "extract_remove",
        "promotion": "extract_promotion",
        "calculate": "cart_calculate",
        "unknown": "unknown_cart_action",
    },
)


# ============================================================
# ADD WORKFLOW
# ============================================================

domain_builder.add_conditional_edges(
    "extract_add",
    route_after_add_extraction,
    {
        "continue": "resolve_variant",
        "error": "graph_error",
    },
)

domain_builder.add_conditional_edges(
    "resolve_variant",
    route_after_variant_resolution,
    {
        "continue": "cart_add",
        "error": "graph_error",
    },
)


# ============================================================
# UPDATE WORKFLOW
# ============================================================

domain_builder.add_conditional_edges(
    "extract_update",
    route_after_update_extraction,
    {
        "continue": "cart_update",
        "error": "graph_error",
    },
)


# ============================================================
# REMOVE WORKFLOW
# ============================================================

domain_builder.add_conditional_edges(
    "extract_remove",
    route_after_remove_extraction,
    {
        "continue": "resolve_remove_line",
        "error": "graph_error",
    },
)

domain_builder.add_conditional_edges(
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

domain_builder.add_conditional_edges(
    "extract_promotion",
    route_after_promotion_extraction,
    {
        "continue": "cart_promotion",
        "error": "graph_error",
    },
)


# ============================================================
# CONDITIONAL INVENTORY -> ADD WORKFLOW
# ============================================================

domain_builder.add_conditional_edges(
    "conditional_extract",
    lambda state: (
        "error"
        if state.get("error")
        else "continue"
    ),
    {
        "continue": "conditional_resolve",
        "error": "graph_error",
    },
)

domain_builder.add_conditional_edges(
    "conditional_resolve",
    lambda state: (
        "error"
        if state.get("error")
        else "continue"
    ),
    {
        "continue": "conditional_inventory_check",
        "error": "graph_error",
    },
)

domain_builder.add_conditional_edges(
    "conditional_inventory_check",
    route_after_inventory_check,
    {
        "available": "conditional_add",
        "unavailable": "conditional_unavailable",
        "error": "graph_error",
    },
)


# ============================================================
# DOMAIN TERMINAL EDGES
# ============================================================

domain_builder.add_edge(
    "product",
    END,
)

domain_builder.add_edge(
    "knowledge",
    END,
)

domain_builder.add_edge(
    "cart_view",
    END,
)

domain_builder.add_edge(
    "cart_add",
    END,
)

domain_builder.add_edge(
    "cart_update",
    END,
)

domain_builder.add_edge(
    "cart_remove",
    END,
)

domain_builder.add_edge(
    "cart_promotion",
    END,
)

domain_builder.add_edge(
    "cart_calculate",
    END,
)

domain_builder.add_edge(
    "conditional_add",
    END,
)

domain_builder.add_edge(
    "conditional_unavailable",
    END,
)

domain_builder.add_edge(
    "unknown_intent",
    END,
)

domain_builder.add_edge(
    "unknown_cart_action",
    END,
)

domain_builder.add_edge(
    "graph_error",
    END,
)


# ============================================================
# COMPILE SINGLE-DOMAIN GRAPH
# ============================================================

domain_graph = (
    domain_builder.compile()
)


# ============================================================
# MULTI-INTENT TASK EXECUTOR
# ============================================================


def execute_planned_tasks_node(
    state: CommerceState,
) -> dict[str, Any]:
    """
    Execute all tasks produced by the commerce planner.

    Each task receives an isolated state so that data from one
    domain does not leak into another domain.

    Example:

    Product + Cart:

        task 1 -> Product domain
        task 2 -> Cart domain

    Cart + Knowledge:

        task 1 -> Cart domain
        task 2 -> Knowledge domain

    Responses are combined after every requested task has been
    processed.
    """

    tasks = state.get(
        "tasks",
        [],
    )

    if not tasks:

        logger.warning(
            "Commerce planner returned no tasks."
        )

        response = (
            "I could not determine what commerce "
            "operation to perform."
        )

        return {
            "response": response,
            "messages": [
                AIMessage(
                    content=response
                )
            ],
            "cart_changed": False,
            "task_results": [],
            "error": (
                "Commerce planner returned no tasks."
            ),
        }

    logger.info(
        "Executing %s planned commerce task(s).",
        len(tasks),
    )

    responses: list[str] = []

    task_results: list[
        dict[str, Any]
    ] = []

    overall_cart_changed = False

    current_cart_id = state.get(
        "cart_id"
    )

    last_intent = "unknown"

    last_cart_action = "unknown"

    # ========================================================
    # EXECUTE TASKS IN USER REQUEST ORDER
    # ========================================================

    for index, task in enumerate(
        tasks,
        start=1,
    ):

        task_query = (
            task.get(
                "query",
                "",
            )
            .strip()
        )

        planned_intent = task.get(
            "intent",
            "auto",
        )

        if not task_query:

            logger.warning(
                "Skipping empty planner task at index %s.",
                index,
            )

            continue

        logger.info(
            (
                "Executing planned task %s/%s. "
                "planned_intent=%s query=%r"
            ),
            index,
            len(tasks),
            planned_intent,
            task_query,
        )

        # ====================================================
        # CREATE ISOLATED TASK STATE
        # ====================================================

        task_intent = (
            planned_intent
            if planned_intent
            in {
                "product",
                "knowledge",
                "cart",
                "conditional",
            }
            else "unknown"
        )

        task_state: CommerceState = {
            "user_message": task_query,
            "cart_id": current_cart_id,
            "intent": task_intent,
            "cart_action": "unknown",
            "cart_changed": False,
            "error": None,
        }

        # ====================================================
        # EXECUTE DOMAIN GRAPH
        # ====================================================

        try:

            task_result = (
                domain_graph.invoke(
                    task_state
                )
            )

        except Exception as exc:

            logger.exception(
                (
                    "Planned task execution failed. "
                    "task=%s query=%r"
                ),
                index,
                task_query,
            )

            task_response = (
                "Unable to complete this request: "
                f"{task_query}"
            )

            responses.append(
                task_response
            )

            task_results.append(
                {
                    "intent": planned_intent,
                    "query": task_query,
                    "response": task_response,
                    "cart_changed": False,
                    "error": str(exc),
                }
            )

            # Tasks in the current implementation are
            # independent, so continue with the remaining tasks.
            continue

        # ====================================================
        # PROPAGATE CART ID
        # ====================================================

        result_cart_id = task_result.get(
            "cart_id"
        )

        if result_cart_id:

            current_cart_id = (
                result_cart_id
            )

        # ====================================================
        # TRACK CART MUTATION
        # ====================================================

        task_cart_changed = bool(
            task_result.get(
                "cart_changed",
                False,
            )
        )

        overall_cart_changed = (
            overall_cart_changed
            or task_cart_changed
        )

        # ====================================================
        # TASK RESPONSE
        # ====================================================

        task_response = (
            task_result.get(
                "response"
            )
            or task_result.get(
                "error"
            )
        )

        if task_response:

            normalized_task_response = (
                str(
                    task_response
                )
                .strip()
            )

            if normalized_task_response:

                responses.append(
                    normalized_task_response
                )

        else:

            normalized_task_response = ""

        executed_intent = (
            task_result.get(
                "intent",
                planned_intent,
            )
        )

        executed_cart_action = (
            task_result.get(
                "cart_action",
                "unknown",
            )
        )

        # ====================================================
        # RECORD TASK RESULT
        # ====================================================

        task_results.append(
            {
                "intent": executed_intent,
                "query": task_query,
                "response": (
                    normalized_task_response
                ),
                "cart_changed": (
                    task_cart_changed
                ),
                "error": task_result.get(
                    "error"
                ),
            }
        )

        last_intent = (
            executed_intent
        )

        last_cart_action = (
            executed_cart_action
        )

        logger.info(
            (
                "Completed planned task %s/%s. "
                "executed_intent=%s "
                "cart_action=%s "
                "cart_changed=%s"
            ),
            index,
            len(tasks),
            executed_intent,
            executed_cart_action,
            task_cart_changed,
        )

    # ========================================================
    # RESPONSE VALIDATION
    # ========================================================

    if not responses:

        logger.warning(
            "No planned task produced a response."
        )

        response = (
            "I was unable to complete the requested tasks."
        )

        return {
            "response": response,
            "messages": [
                AIMessage(
                    content=response
                )
            ],
            "cart_changed": overall_cart_changed,
            "task_results": task_results,
            "cart_id": current_cart_id,
            "error": (
                "No task produced a response."
            ),
        }

    # ========================================================
    # RESPONSE AGGREGATION
    # ========================================================

    final_response = (
        "\n\n".join(
            responses
        )
    )

    # Preserve normal single-domain intent for simple queries.
    #
    # Mixed requests are clearly identified as multi.
    if len(tasks) == 1:

        final_intent = (
            last_intent
        )

        final_cart_action = (
            last_cart_action
        )

    else:

        final_intent = "multi"

        final_cart_action = "unknown"

    logger.info(
        (
            "Planned task execution completed. "
            "task_count=%s final_intent=%s "
            "cart_changed=%s"
        ),
        len(tasks),
        final_intent,
        overall_cart_changed,
    )

    return {
        "response": final_response,

        # Persist the assistant turn in the same LangGraph thread.
        # Because CommerceState.messages uses add_messages, this
        # AIMessage is appended to the conversation checkpoint.
        "messages": [
            AIMessage(
                content=final_response
            )
        ],

        "intent": final_intent,
        "cart_action": final_cart_action,
        "cart_changed": overall_cart_changed,
        "cart_id": current_cart_id,
        "task_results": task_results,
        "error": None,
    }


# ============================================================
# OUTER MULTI-INTENT ORCHESTRATION GRAPH
# ============================================================

orchestration_builder = StateGraph(
    CommerceState
)


# ============================================================
# ORCHESTRATION NODES
# ============================================================

orchestration_builder.add_node(
    "planner",
    plan_tasks_node,
)

orchestration_builder.add_node(
    "task_executor",
    execute_planned_tasks_node,
)


# ============================================================
# ORCHESTRATION EDGES
# ============================================================

orchestration_builder.add_edge(
    START,
    "planner",
)

orchestration_builder.add_edge(
    "planner",
    "task_executor",
)

orchestration_builder.add_edge(
    "task_executor",
    END,
)


# ============================================================
# PUBLIC COMMERCE GRAPH
# ============================================================

commerce_graph = (
    orchestration_builder.compile()
)