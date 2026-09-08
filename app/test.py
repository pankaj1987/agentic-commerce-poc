from app.config.llm import get_llm

llm = get_llm()
response = llm.invoke(
    "Explain Google UCP in two sentences."
)

print(response.content)