from langchain.agents import create_agent

from app.config.llm import get_llm
from app.prompts.order import ORDER_AGENT_SYSTEM_PROMPT
from app.tools.knowledge_tools import search_knowledge
from app.tools.order_tools import (
    lookup_order,
    get_order_status,
    get_order_details,
    get_order_history,
    check_order_cancellation_eligibility,
    check_order_return_eligibility,
)


model = get_llm()

order_agent = create_agent(
    model=model,
    tools=[
        lookup_order,
        get_order_status,
        get_order_details,
        get_order_history,
        check_order_cancellation_eligibility,
        check_order_return_eligibility,
        search_knowledge,
    ],
    system_prompt=ORDER_AGENT_SYSTEM_PROMPT,
)
