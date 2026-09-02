from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


COLLECTION_NAME = "commerce_knowledge"


def get_vector_store() -> Chroma:
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )

    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory="./chroma_db",
        embedding_function=embeddings,
    )