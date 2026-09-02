from langchain_core.tools import tool

from app.rag.retriever import search_knowledge_documents


def detect_knowledge_scope(
    query: str,
) -> tuple[str | None, str | None]:
    """
    Determine whether the query can be narrowed using
    knowledge-base metadata.

    Returns:
        (category, product_name)
    """

    query_lower = query.lower()

    # --------------------------------
    # Product-specific knowledge
    # --------------------------------

    if "athletic running shoes" in query_lower:
        return "product", "Athletic Running Shoes"

    if (
        "memory foam" in query_lower
        or "ultrasoft outsole" in query_lower
    ):
        return (
            "product",
            "Running Shoe with Memory Foam Insole "
            "& Ultrasoft Outsole",
        )

    # --------------------------------
    # Promotion
    # --------------------------------

    if (
        "promotion" in query_lower
        or "promo" in query_lower
        or "discount" in query_lower
        or "coupon" in query_lower
        or "promotion code" in query_lower
        or "save20" in query_lower
        or "20%" in query_lower
    ):
        return "promotion", None

    # --------------------------------
    # Return policy
    # --------------------------------

    if (
        "return" in query_lower
        or "refund" in query_lower
        or "non-returnable" in query_lower
    ):
        return "return_policy", None

    # --------------------------------
    # Delivery
    # --------------------------------

    if (
        "delivery" in query_lower
        or "delivered" in query_lower
        or "delivery time" in query_lower
    ):
        return "delivery_policy", None

    # --------------------------------
    # Shipping
    # --------------------------------

    if (
        "shipping" in query_lower
        or "shipment" in query_lower
        or "shipping cost" in query_lower
    ):
        return "shipping_policy", None

    # --------------------------------
    # Order split
    # --------------------------------

    if (
        "split order" in query_lower
        or "order split" in query_lower
        or "split shipment" in query_lower
        or "two shipments" in query_lower
    ):
        return "order_split", None

    return None, None


@tool
def search_knowledge(query: str) -> str:
    """
    Search the commerce knowledge base for authoritative static information.

    ALWAYS use this tool for:
    - return policy
    - refund policy
    - shipping policy
    - delivery policy
    - promotion rules
    - product benefits
    - order split reasons
    - other static commerce policies

    For a general question such as "What is the return policy?",
    search directly using "return policy". Do not ask the customer
    for a product unless the retrieved policy specifically requires
    product-specific information.
    """

    category, product_name = detect_knowledge_scope(query)

    documents = search_knowledge_documents(
        query=query,
        category=category,
        product_name=product_name,
    )

    if not documents:
        return (
            "No relevant information was found in the "
            "commerce knowledge base."
        )

    results = []

    for document in documents:
        results.append(document.page_content)

    return "\n\n---\n\n".join(results)