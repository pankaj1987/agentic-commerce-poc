# app/services/session_service.py

from app.persistence.models import CommerceSession
from app.persistence.repositories.session_repository import (
    SessionRepository,
)


class SessionService:
    """
    Application service responsible for resolving the public
    session_id used by the API into a persisted CommerceSession.

    session_id:
        Public application/session identifier.

    thread_id:
        Internal LangGraph checkpoint identifier.

    They are intentionally different identifiers.
    """

    @staticmethod
    def get_or_create_session(
        session_id: str | None,
        user_id: str | None = None,
    ) -> CommerceSession:
        # First request: create a new commerce session.
        if not session_id:
            return (
                SessionRepository.create_session(
                    user_id=user_id
                )
            )

        normalized_session_id = (
            session_id.strip()
        )

        if not normalized_session_id:
            return (
                SessionRepository.create_session(
                    user_id=user_id
                )
            )

        commerce_session = (
            SessionRepository.get_session(
                normalized_session_id
            )
        )

        # Production behavior:
        # do not silently create a replacement session when a client
        # supplies an unknown identifier. Doing so would unexpectedly
        # lose conversation continuity and could hide client bugs.
        if commerce_session is None:
            raise ValueError(
                "The commerce session does not exist or has expired."
            )

        if commerce_session.status != "ACTIVE":
            raise ValueError(
                "The commerce session is not active."
            )

        # Future authentication enhancement:
        # when user_id is mandatory, validate ownership here.
        if (
            user_id is not None
            and commerce_session.user_id is not None
            and commerce_session.user_id != user_id
        ):
            raise PermissionError(
                "The commerce session does not belong to this user."
            )

        return commerce_session
