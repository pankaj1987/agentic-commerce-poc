from langchain_ollama import OllamaEmbeddings


def get_embeddings():
    return OllamaEmbeddings(
        model="qwen3-embedding:0.6b"
    )