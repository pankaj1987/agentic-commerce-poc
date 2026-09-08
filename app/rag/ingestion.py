from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.vector_store import get_vector_store
from app.security.rag_security import RagSecurityService


KNOWLEDGE_BASE_PATH = Path(
    "knowledge/commerce_knowledge_base.md"
)


def load_knowledge_documents() -> list[Document]:
    content = KNOWLEDGE_BASE_PATH.read_text(
        encoding="utf-8"
    )

    sections = content.split("\n---\n")

    documents = []

    for section in sections:
        section = section.strip()

        if not section:
            continue

        # Knowledge is data, not executable instruction. Reject sections that
        # contain prompt/tool/secret-exfiltration patterns before indexing.
        if RagSecurityService.is_suspicious_content(section):
            continue

        metadata = extract_metadata(section)
        metadata["security_boundary"] = "untrusted_reference_data"

        documents.append(
            Document(
                page_content=section,
                metadata=metadata,
            )
        )

    return documents


def extract_metadata(section: str) -> dict:
    """
    Extract metadata from each knowledge section.
    """

    metadata = {
        "category": "general"
    }

    first_heading = None

    for line in section.splitlines():
        line = line.strip()

        if line.startswith("## "):
            first_heading = line[3:].strip()
            break

    if not first_heading:
        return metadata

    heading_lower = first_heading.lower()

    # -------------------------
    # Promotion
    # -------------------------
    if "promotion" in heading_lower:
        metadata["category"] = "promotion"

    # -------------------------
    # Return policy
    # -------------------------
    elif "return" in heading_lower:
        metadata["category"] = "return_policy"

    # -------------------------
    # Delivery policy
    # -------------------------
    elif "delivery" in heading_lower:
        metadata["category"] = "delivery_policy"

    # -------------------------
    # Shipping policy
    # -------------------------
    elif "shipping" in heading_lower:
        metadata["category"] = "shipping_policy"

    # -------------------------
    # Order split
    # -------------------------
    elif "order split" in heading_lower:
        metadata["category"] = "order_split"

    # -------------------------
    # Product knowledge
    # -------------------------
    elif "product knowledge" in heading_lower:
        metadata["category"] = "product"

        if "athletic running shoes" in heading_lower:
            metadata["product_name"] = "Athletic Running Shoes"

        elif "memory foam" in heading_lower:
            metadata["product_name"] = (
                "Running Shoe with Memory Foam Insole "
                "& Ultrasoft Outsole"
            )

    return metadata


def ingest_documents():
    documents = load_knowledge_documents()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    )

    chunks = splitter.split_documents(documents)

    vector_store = get_vector_store()

    vector_store.add_documents(chunks)

    print(
        f"Ingested {len(documents)} knowledge sections "
        f"into {len(chunks)} chunks."
    )


if __name__ == "__main__":
    ingest_documents()