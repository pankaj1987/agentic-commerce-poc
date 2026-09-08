# app/persistence/checkpointer.py

import logging
from threading import Lock

from langgraph.checkpoint.postgres import (
    PostgresSaver,
)

from psycopg import Connection
from psycopg.rows import dict_row

from app.config.settings import (
    settings,
)


logger = logging.getLogger(__name__)


# ============================================================
# SINGLETON STATE
# ============================================================
#
# The LangGraph checkpointer must remain alive for the lifetime
# of the FastAPI process because the compiled CommerceGraph
# keeps a reference to it.
#
# Do NOT use:
#
# PostgresSaver.from_conn_string(...)
#
# as a normal constructor. It returns a context manager.
#
# Instead, create a long-lived Psycopg connection explicitly
# and pass it directly to PostgresSaver.
# ============================================================

_checkpointer: PostgresSaver | None = None

_checkpoint_connection: Connection | None = None

_initialization_lock = Lock()


# ============================================================
# GET CHECKPOINTER
# ============================================================

def get_checkpointer() -> PostgresSaver:
    """
    Return the application-wide LangGraph Postgres checkpointer.

    The first call:

    1. Opens a PostgreSQL connection.
    2. Creates PostgresSaver.
    3. Runs LangGraph checkpoint migrations/setup.
    4. Keeps the connection alive for the FastAPI process.

    Subsequent calls return the same checkpointer.
    """

    global _checkpointer
    global _checkpoint_connection

    if _checkpointer is not None:
        return _checkpointer

    with _initialization_lock:

        # Another thread may have initialized it while
        # this thread was waiting for the lock.
        if _checkpointer is not None:
            return _checkpointer

        logger.info(
            "Initializing LangGraph PostgreSQL checkpointer."
        )

        connection_string = (
            settings.langgraph_checkpoint_database_url
            or ""
        ).strip()

        if not connection_string:
            raise RuntimeError(
                "LANGGRAPH_CHECKPOINT_DATABASE_URL "
                "is not configured."
            )

        # SQLAlchemy uses the driver-qualified URL form:
        #
        #     postgresql+psycopg://...
        #
        # Psycopg itself expects the standard PostgreSQL URI:
        #
        #     postgresql://...
        #
        # Accept either form so DATABASE_URL and the checkpoint URL can
        # safely point at the same database without making application
        # startup depend on SQLAlchemy-specific syntax.
        if connection_string.startswith(
            "postgresql+psycopg://"
        ):
            connection_string = connection_string.replace(
                "postgresql+psycopg://",
                "postgresql://",
                1,
            )
        elif connection_string.startswith(
            "postgres+psycopg://"
        ):
            connection_string = connection_string.replace(
                "postgres+psycopg://",
                "postgresql://",
                1,
            )

        try:
            # LangGraph PostgresSaver requires:
            #
            # autocommit=True
            #     setup() creates/migrates checkpoint tables and
            #     those operations must be committed.
            #
            # row_factory=dict_row
            #     PostgresSaver accesses query results using
            #     dictionary-style column access.

            _checkpoint_connection = (
                Connection.connect(
                    connection_string,
                    autocommit=True,
                    row_factory=dict_row,
                )
            )

            _checkpointer = PostgresSaver(
                _checkpoint_connection
            )

            # Safe to run repeatedly.
            #
            # For a larger production deployment this can later
            # be moved into a deployment/migration step.
            _checkpointer.setup()

            logger.info(
                "LangGraph PostgreSQL checkpointer initialized."
            )

            return _checkpointer

        except Exception:

            logger.exception(
                "Unable to initialize LangGraph "
                "PostgreSQL checkpointer."
            )

            if _checkpoint_connection is not None:

                try:
                    _checkpoint_connection.close()

                except Exception:
                    logger.exception(
                        "Unable to close failed checkpoint "
                        "database connection."
                    )

            _checkpoint_connection = None
            _checkpointer = None

            raise


# ============================================================
# CLOSE CHECKPOINTER
# ============================================================

def close_checkpointer() -> None:
    """
    Close the PostgreSQL connection used by LangGraph.

    Intended to be called during FastAPI application shutdown.
    """

    global _checkpointer
    global _checkpoint_connection

    with _initialization_lock:

        if _checkpoint_connection is not None:

            logger.info(
                "Closing LangGraph PostgreSQL "
                "checkpointer connection."
            )

            try:
                _checkpoint_connection.close()

            finally:
                _checkpoint_connection = None
                _checkpointer = None

            logger.info(
                "LangGraph PostgreSQL "
                "checkpointer connection closed."
            )