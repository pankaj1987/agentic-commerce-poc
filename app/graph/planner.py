# app/graph/planner.py

import logging
from typing import Literal

from pydantic import BaseModel, Field

from app.config.llm import get_llm
from app.graph.state import CommerceState
from app.utils.message_utils import extract_message_text


logger = logging.getLogger(__name__)


class PlannedTask(BaseModel):
    intent: Literal[
        "product",
        "knowledge",
        "cart",
        "conditional",
    ] = Field(
        description=(
            "Commerce domain that should execute this task."
        )
    )

    query: str = Field(
        min_length=1,
        description=(
            "Self-contained task query containing all information "
            "needed by the selected domain."
        ),
    )


class CommercePlan(BaseModel):
    tasks: list[PlannedTask] = Field(
        min_length=1,
        description=(
            "Tasks to execute sequentially in the same logical "
            "order as the customer's request."
        ),
    )


def _message_role(message) -> str:
    """
    Convert LangChain message types to customer-friendly role names.
    """

    message_type = getattr(
        message,
        "type",
        "message",
    )

    mapping = {
        "human": "Customer",
        "ai": "Assistant",
        "system": "System",
        "tool": "Tool",
    }

    return mapping.get(
        message_type,
        str(message_type).title(),
    )


def _format_recent_history(
    state: CommerceState,
    max_messages: int = 8,
) -> str:
    """
    Return recent PREVIOUS conversation turns for reference
    resolution.

    The current HumanMessage is already inserted into state before
    the planner runs. It is intentionally excluded from the history
    section when it matches state['user_message'] so that the current
    request is not duplicated in the planner prompt.
    """

    messages = list(
        state.get(
            "messages",
            [],
        )
        or []
    )

    if not messages:
        return "(No previous conversation.)"

    current_user_message = (
        state.get(
            "user_message",
            "",
        )
        .strip()
    )

    # Exclude the current HumanMessage from "previous history".
    if messages:
        last_message = messages[-1]

        last_type = getattr(
            last_message,
            "type",
            None,
        )

        last_text = extract_message_text(
            last_message
        ).strip()

        if (
            last_type == "human"
            and current_user_message
            and last_text == current_user_message
        ):
            messages = messages[:-1]

    messages = messages[
        -max_messages:
    ]

    if not messages:
        return "(No previous conversation.)"

    history_lines: list[str] = []

    for message in messages:
        text = extract_message_text(
            message
        ).strip()

        if not text:
            continue

        history_lines.append(
            f"{_message_role(message)}: {text}"
        )

    if not history_lines:
        return "(No previous conversation.)"

    return "\n".join(
        history_lines
    )


def plan_tasks_node(
    state: CommerceState,
) -> dict:
    """
    Convert the current customer request into one or more
    sequential commerce tasks.

    Conversation history is used only to resolve references
    contained in the CURRENT request. Previous actions must never
    be repeated merely because they appear in history.
    """

    logger.info(
        "Executing commerce planner."
    )

    user_message = (
        state.get(
            "user_message",
            "",
        )
        .strip()
    )

    if not user_message:
        return {
            "tasks": [],
            "error": (
                "No user message was provided."
            ),
        }

    recent_history = (
        _format_recent_history(
            state
        )
    )

    llm = get_llm()

    structured_llm = (
        llm.with_structured_output(
            CommercePlan
        )
    )

    prompt = f"""
You are the planning layer for an agentic commerce system.

Your job is to convert the CURRENT customer request into one or more
self-contained tasks.

The available domains are:

1. product
   Use for live product/catalog/inventory questions.

   Examples:
   - search for products
   - product details
   - current price
   - current inventory
   - whether a product or variant is in stock

2. knowledge
   Use for static commerce knowledge stored in the knowledge base.

   Examples:
   - return policy
   - shipping policy
   - delivery policy
   - promotion rules
   - product benefits
   - order split policy

3. cart
   Use for shopping-cart operations.

   Examples:
   - show/view cart
   - add item
   - remove item
   - change quantity
   - apply promotion
   - cart subtotal
   - cart total

4. conditional
   Use ONLY for a supported dependent commerce workflow where a
   cart mutation depends on a live inventory result.

   Currently supported conditional workflow:

       CHECK INVENTORY
              ->
       IF enough inventory exists
              ->
       ADD requested quantity to cart

   Example:
   "Check whether Athletic Running Shoes US 8 / Black is in stock.
    If it is in stock, add 2 to my cart."

   This MUST be emitted as ONE conditional task.

============================================================
CONVERSATION HISTORY RULES
============================================================

Recent conversation may be used ONLY to resolve references in the
CURRENT customer request.

Examples of references that may require history:
- "add another one"
- "add 2 of those"
- "make that 3"
- "is the black one available?"
- "what is its return policy?"
- "add the one you just showed me"

When history clearly identifies the referenced product, variant,
quantity, or subject, rewrite the planned task so it is self-contained.

Example:

Previous conversation:
Customer: Is Athletic Running Shoes US 8 / Black in stock?
Assistant: Yes, it is available.

Current request:
"Add 2 of those."

Good planned task:
intent = cart
query = "Add 2 Athletic Running Shoes US 8 / Black to my cart."

CRITICAL:
- Do NOT repeat a previous action merely because it appears in history.
- Do NOT re-run an earlier add/remove/update/promotion operation unless
  the CURRENT customer request asks for it.
- History is context, not a task list.
- Current Shopify APIs remain the source of truth for live commerce data.
- Do not infer missing product details when history does not clearly
  identify them.

============================================================
MULTI-INTENT RULES
============================================================

If the customer asks for multiple INDEPENDENT things, create multiple
tasks in the same order as the customer's request.

Example:

"Is Athletic Running Shoes in stock and add Athletic Running Shoes
 US 8 / Black to my cart."

This has no dependency phrase such as "if it is in stock".

Plan:
1. product task for inventory
2. cart task for add

Example:

"Add Athletic Running Shoes US 8 / Black and tell me the return policy."

Plan:
1. cart task
2. knowledge task

============================================================
CONDITIONAL RULES
============================================================

If words such as:
- if
- only if
- provided that
- when it is available

make the ADD operation depend on the inventory result, create exactly
ONE conditional task.

Do NOT split a dependent inventory -> add request into separate product
and cart tasks.

============================================================
SELF-CONTAINED TASK RULES
============================================================

Every task query must contain enough information for the selected
domain to execute it.

Resolve references from conversation history only when the reference is
clear.

Do not invent:
- product names
- variants
- quantities
- promotion codes
- policies
- cart contents
- inventory

============================================================
RECENT PREVIOUS CONVERSATION
============================================================

{recent_history}

============================================================
CURRENT CUSTOMER REQUEST
============================================================

{user_message}
"""

    try:
        plan = structured_llm.invoke(
            prompt
        )

    except Exception:
        logger.exception(
            "Commerce planner failed."
        )

        # The outer graph can still fall back to its deterministic
        # routing when the planner cannot produce structured output.
        return {
            "tasks": [
                {
                    "intent": "auto",
                    "query": user_message,
                }
            ],
            "error": None,
        }

    tasks = [
        {
            "intent": task.intent,
            "query": task.query.strip(),
        }
        for task in plan.tasks
        if task.query.strip()
    ]

    if not tasks:
        logger.warning(
            "Commerce planner produced an empty task list."
        )

        return {
            "tasks": [
                {
                    "intent": "auto",
                    "query": user_message,
                }
            ],
            "error": None,
        }

    logger.info(
        "Commerce planner produced %s task(s).",
        len(tasks),
    )

    return {
        "tasks": tasks,
        "error": None,
    }
