# app/graph/knowledge_node.py

import logging

from app.config.llm import get_llm
from app.graph.state import CommerceState
from app.rag.retriever import get_retriever
from app.utils.message_utils import extract_message_text


logger = logging.getLogger(__name__)


def knowledge_node(
    state: CommerceState,
) -> dict:

    logger.info(
        "Executing Knowledge node."
    )

    query = state["user_message"]

    retriever = get_retriever()

    documents = retriever.invoke(
        query
    )

    if not documents:
        return {
            "response": (
                "I could not find relevant information "
                "in the commerce knowledge base."
            ),
            "cart_changed": False,
        }

    context = "\n\n---\n\n".join(
        document.page_content
        for document in documents
    )

    llm = get_llm()

    prompt = f"""
You are a commerce knowledge assistant.

Answer the customer's question using ONLY
the supplied knowledge-base context.

Do not invent information.

If the context does not contain enough
information to answer the question,
say that the information is not available.

Customer question:

{query}

Knowledge-base context:

{context}
"""

    result = llm.invoke(
        prompt
    )

    response = extract_message_text(
        result
    )

    return {
        "response": response,
        "cart_changed": False,
    }