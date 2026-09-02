from app.tools.knowledge_tools import search_knowledge


def test_search_knowledge():

    result = search_knowledge.invoke(
        {
            "query": "What are the benefits of Athletic Running Shoes?"
        }
    )

    print("\nRAG Result:")
    print(result)

    assert result