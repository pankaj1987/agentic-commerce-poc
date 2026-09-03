# app/graph/planner.py

import logging
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)

from app.config.llm import get_llm
from app.graph.state import CommerceState


logger = logging.getLogger(__name__)


# ============================================================
# STRUCTURED PLANNER OUTPUT
# ============================================================


class PlannedTask(BaseModel):

    intent: Literal[
        "product",
        "knowledge",
        "cart",
        "conditional",
    ] = Field(
        description=(
            "Commerce domain or controlled workflow "
            "responsible for this task."
        )
    )

    query: str = Field(
        min_length=1,
        description=(
            "Self-contained request that should be "
            "executed by the selected domain/workflow."
        ),
    )


class CommercePlan(BaseModel):

    tasks: list[PlannedTask] = Field(
        min_length=1,
        description=(
            "All requested commerce tasks in execution order."
        ),
    )


# ============================================================
# PLANNER
# ============================================================


def plan_tasks_node(
    state: CommerceState,
) -> dict:

    logger.info(
        "Executing multi-intent commerce planner."
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
            "error": (
                "No user message was provided."
            ),
            "tasks": [],
        }

    llm = get_llm()

    structured_llm = (
        llm.with_structured_output(
            CommercePlan
        )
    )

    prompt = f"""
You are the planning layer of an e-commerce AI system.

Decompose the customer's request into one or more executable
commerce tasks.

Available task types:

1. product

Use for:
- product search
- product details
- inventory questions
- stock availability
- variant availability
- prices

2. knowledge

Use for STATIC knowledge:
- return policy
- refund policy
- shipping policy
- delivery policy
- promotion rules
- product benefits
- order split explanations

3. cart

Use for:
- show cart
- add to cart
- remove from cart
- update quantity
- cart subtotal
- cart total
- amount to pay
- apply promotion code

4. conditional

Use when a later commerce operation MUST happen only if
a previous condition is true.

Currently supported conditional workflow:

INVENTORY -> ADD TO CART

Examples:

"Check whether US 8 / Black is in stock.
If it is in stock, add 2 to my cart."

"If Athletic Running Shoes US 8 / Black is available,
add 2 to my cart."

"Add 2 Athletic Running Shoes US 8 / Black only if
they are in stock."

These MUST be ONE conditional task.

Do NOT split them into independent product and cart tasks,
because the cart mutation depends on inventory.

IMPORTANT RULES:

- Extract every independently requested task.
- Preserve execution order.
- Each query must be self-contained.
- Do not answer the customer.
- Do not execute tools.
- Do not invent requests.
- Do not split one logical conditional workflow.
- When "if", "only if", "provided that", or equivalent wording
  makes a mutation dependent on inventory, use conditional.

Examples:


Customer:
"What is the return policy?"

Tasks:
[
  {{
    "intent": "knowledge",
    "query": "What is the return policy?"
  }}
]


Customer:
"Is Athletic Running Shoes in stock?"

Tasks:
[
  {{
    "intent": "product",
    "query": "Is Athletic Running Shoes in stock?"
  }}
]


Customer:
"Add Athletic Running Shoes US 8 / Black to my cart."

Tasks:
[
  {{
    "intent": "cart",
    "query":
      "Add Athletic Running Shoes US 8 / Black to my cart."
  }}
]


Customer:
"Is Athletic Running Shoes in stock and add
Athletic Running Shoes US 8 / Black to my cart."

There is no conditional wording, so these are independent:

[
  {{
    "intent": "product",
    "query": "Is Athletic Running Shoes in stock?"
  }},
  {{
    "intent": "cart",
    "query":
      "Add Athletic Running Shoes US 8 / Black to my cart."
  }}
]


Customer:
"Check whether Athletic Running Shoes US 8 / Black
is in stock. If it is in stock, add 2 to my cart."

Tasks:
[
  {{
    "intent": "conditional",
    "query":
      "Check whether Athletic Running Shoes US 8 / Black "
      "is in stock. If it is in stock, add 2 to my cart."
  }}
]


Customer:
"Add 2 Athletic Running Shoes US 8 / Black to my cart.
What is the return policy?"

Tasks:
[
  {{
    "intent": "cart",
    "query":
      "Add 2 Athletic Running Shoes US 8 / Black to my cart."
  }},
  {{
    "intent": "knowledge",
    "query": "What is the return policy?"
  }}
]


Customer request:

{user_message}
"""

    try:

        plan = structured_llm.invoke(
            prompt
        )

    except Exception:

        logger.exception(
            "Multi-intent planner failed."
        )

        return {
            "tasks": [
                {
                    "intent": "auto",
                    "query": user_message,
                }
            ]
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
        return {
            "tasks": [
                {
                    "intent": "auto",
                    "query": user_message,
                }
            ]
        }

    logger.info(
        "Planner created %s task(s): %s",
        len(tasks),
        [
            task["intent"]
            for task in tasks
        ],
    )

    return {
        "tasks": tasks
    }