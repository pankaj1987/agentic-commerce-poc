from app.rag.retriever import get_retriever


def test_rag_retrieval():
    retriever = get_retriever()

    results = retriever.invoke(
        "Why wasn't my 20% promotion applied?"
    )

    print("\nRetrieved documents:\n")

    for doc in results:
        print("--------------------------------")
        print(doc.page_content)
        print(doc.metadata)