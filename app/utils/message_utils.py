# app/utils/message_utils.py

def extract_message_text(
    message,
) -> str:

    content = getattr(
        message,
        "content",
        None,
    )

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):

        parts = []

        for block in content:

            if isinstance(block, str):
                parts.append(block)

            elif isinstance(block, dict):

                text = block.get("text")

                if text:
                    parts.append(
                        str(text)
                    )

        return "\n".join(
            parts
        ).strip()

    if content is None:
        return ""

    return str(content).strip()