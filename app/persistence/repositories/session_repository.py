# app/persistence/repositories/session_repository.py

from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import select

from app.persistence.database import (
    SessionLocal,
)
from app.persistence.models import (
    CommerceSession,
)


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


class SessionRepository:

    # ============================================================
    # CREATE SESSION
    # ============================================================

    @staticmethod
    def create_session(
        user_id: str | None = None,
    ) -> CommerceSession:

        with SessionLocal() as db:

            commerce_session = (
                CommerceSession(
                    user_id=user_id,
                )
            )

            db.add(
                commerce_session
            )

            db.commit()

            db.refresh(
                commerce_session
            )

            return commerce_session

    # ============================================================
    # GET SESSION
    # ============================================================

    @staticmethod
    def get_session(
        session_id: str,
    ) -> CommerceSession | None:

        with SessionLocal() as db:

            statement = (
                select(
                    CommerceSession
                )
                .where(
                    CommerceSession.session_id
                    == session_id
                )
            )

            return db.scalar(
                statement
            )

    # ============================================================
    # UPDATE CART ASSOCIATION
    # ============================================================

    @staticmethod
    def update_cart_id(
        session_id: str,
        cart_id: str | None,
    ) -> CommerceSession:

        with SessionLocal() as db:

            statement = (
                select(
                    CommerceSession
                )
                .where(
                    CommerceSession.session_id
                    == session_id
                )
            )

            commerce_session = (
                db.scalar(
                    statement
                )
            )

            if commerce_session is None:
                raise ValueError(
                    "Commerce session not found."
                )

            commerce_session.cart_id = (
                cart_id
            )

            now = utc_now()

            commerce_session.last_activity_at = (
                now
            )

            commerce_session.updated_at = (
                now
            )

            db.commit()

            db.refresh(
                commerce_session
            )

            return commerce_session

    # ============================================================
    # TOUCH SESSION
    # ============================================================

    @staticmethod
    def touch_session(
        session_id: str,
    ) -> None:

        with SessionLocal() as db:

            statement = (
                select(
                    CommerceSession
                )
                .where(
                    CommerceSession.session_id
                    == session_id
                )
            )

            commerce_session = (
                db.scalar(
                    statement
                )
            )

            if commerce_session is None:
                return

            now = utc_now()

            commerce_session.last_activity_at = (
                now
            )

            commerce_session.updated_at = (
                now
            )

            db.commit()