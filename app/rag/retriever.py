from app.rag.vector_store import get_vector_store


def get_retriever():
    """
    Return the default commerce knowledge retriever.
    """

    vector_store = get_vector_store()

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 2,
        },
    )


def search_knowledge_documents(
    query: str,
    category: str | None = None,
    product_name: str | None = None,
):
    """
    Search the commerce knowledge base.

    Optional metadata filters can be used to improve retrieval
    precision for product-specific and policy-specific queries.
    """

    vector_store = get_vector_store()

    filters = []

    if category:
        filters.append({
            "category": category
        })

    if product_name:
        filters.append({
            "product_name": product_name
        })

    # No metadata filter
    if not filters:
        return vector_store.similarity_search(
            query,
            k=2,
        )

    # One metadata filter
    if len(filters) == 1:
        return vector_store.similarity_search(
            query,
            k=2,
            filter=filters[0],
        )

    # Multiple metadata filters
    return vector_store.similarity_search(
        query,
        k=2,
        filter={
            "$and": filters
        },
    )