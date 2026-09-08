from app.config.llm import get_llm

llm = get_llm()

def test_search_products():
    print(llm.model_name)
    response = llm.invoke(
        "Explain Google UCP in two sentences."
    )
    print(response.content)



