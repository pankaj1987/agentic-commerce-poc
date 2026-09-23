# app/persistence/models.py

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CommerceSession(Base):
    __tablename__ = "commerce_sessions"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))

    # Phase 5A: every new commerce session is owned by an authenticated app user.
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Shopify opaque cart ID. Do NOT log this value.
    cart_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class CustomerIdentity(Base):
    """Maps an authenticated application user to the authoritative Shopify customer."""

    __tablename__ = "customer_identities"

    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    shopify_customer_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
