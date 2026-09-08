# app/graph/state.py

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class CommerceTask(TypedDict):
    intent: Literal[
        "product",
        "knowledge",
        "cart",
        "conditional",
        "order",
        "auto",
    ]
    query: str


class CommerceTaskResult(TypedDict, total=False):
    intent: str
    query: str
    response: str
    cart_changed: bool
    error: str | None


class CommerceState(TypedDict, total=False):
    # ------------------------------------------------------------
    # CONVERSATION MEMORY
    # ------------------------------------------------------------
    #
    # add_messages is a LangGraph reducer. When the same thread_id
    # is invoked again, newly supplied HumanMessage/AIMessage
    # objects are merged with the messages already stored by the
    # checkpointer rather than replacing them.
    #
    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]

    # Current user request. This remains separate from messages
    # because workflow nodes should operate on the current turn,
    # while messages provides conversation context.
    user_message: str

    # ------------------------------------------------------------
    # COMMERCE STATE
    # ------------------------------------------------------------

    cart_id: str | None

    intent: Literal[
        "product",
        "knowledge",
        "cart",
        "conditional",
        "order",
        "multi",
        "unknown",
    ]

    tasks: list[CommerceTask]
    task_results: list[CommerceTaskResult]

    cart_action: Literal[
        "view",
        "add",
        "update",
        "remove",
        "promotion",
        "calculate",
        "unknown",
    ]

    # ------------------------------------------------------------
    # PRODUCT / CART WORKFLOW FIELDS
    # ------------------------------------------------------------

    product_name: str | None
    variant_title: str | None
    quantity: int | None

    line_id: str | None
    line_number: int | None

    promotion_code: str | None
    resolved_variant_id: str | None

    # ------------------------------------------------------------
    # CONDITIONAL INVENTORY -> ADD WORKFLOW
    # ------------------------------------------------------------

    inventory_checked: bool
    inventory_tracked: bool | None
    inventory_available: bool | None
    available_quantity: int | None

    # ------------------------------------------------------------
    # RESPONSE / EXECUTION STATUS
    # ------------------------------------------------------------

    response: str
    cart_changed: bool
    error: str | None
