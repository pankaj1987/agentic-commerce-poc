# app/graph/state.py

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class CommerceState(TypedDict, total=False):

    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]

    user_message: str

    cart_id: str | None

    intent: Literal[
        "product",
        "knowledge",
        "cart",
        "unknown",
    ]

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

    response: str

    cart_changed: bool

    error: str | None