# app/graph/state.py

from typing import (
    Annotated,
    Literal,
    TypedDict,
)

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class CommerceTask(TypedDict):
    """
    One independently executable task produced by the planner.
    """

    intent: Literal[
        "product",
        "knowledge",
        "cart",
        "conditional",
        "auto",
    ]

    query: str


class CommerceTaskResult(TypedDict, total=False):
    """
    Result of executing one planned task.
    """

    intent: str
    query: str
    response: str
    cart_changed: bool
    error: str | None


class CommerceState(TypedDict, total=False):

    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]

    user_message: str

    cart_id: str | None

    # ========================================================
    # ORCHESTRATION
    # ========================================================

    intent: Literal[
        "product",
        "knowledge",
        "cart",
        "conditional",
        "multi",
        "unknown",
    ]

    tasks: list[CommerceTask]

    task_results: list[
        CommerceTaskResult
    ]

    # ========================================================
    # CART
    # ========================================================

    cart_action: Literal[
        "view",
        "add",
        "update",
        "remove",
        "promotion",
        "calculate",
        "unknown",
    ]

    product_name: str | None
    variant_title: str | None
    quantity: int | None

    line_id: str | None
    line_number: int | None

    promotion_code: str | None

    resolved_variant_id: str | None

    # ========================================================
    # CONDITIONAL INVENTORY WORKFLOW
    # ========================================================

    inventory_checked: bool

    inventory_tracked: bool | None

    inventory_available: bool | None

    available_quantity: int | None

    # ========================================================
    # RESULT
    # ========================================================

    response: str

    cart_changed: bool

    error: str | None