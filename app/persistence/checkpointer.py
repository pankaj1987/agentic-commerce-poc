# app/persistence/checkpointer.py

from langgraph.checkpoint.postgres import (
    PostgresSaver,
)

from app.config.settings import (
    settings,
)


_checkpointer: PostgresSaver | None = None


def get_checkpointer() -> PostgresSaver:

    global _checkpointer

    if _checkpointer is None:

        _checkpointer = (
            PostgresSaver.from_conn_string(
                settings
                .langgraph_checkpoint_database_url
            )
        )

        _checkpointer.setup()

    return _checkpointer