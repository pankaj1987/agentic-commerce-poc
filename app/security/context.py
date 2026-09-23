from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SecurityContext:
    """Authenticated identity used by application services and agent tools.

    The authentication mechanism is intentionally abstract.  In this POC the
    FastAPI dependency can populate the context from trusted development
    headers.  In production the same object should be populated from a
    verified OIDC/JWT identity issued by the enterprise identity provider.
    """

    user_id: str
    shopify_customer_id: str | None = None
    roles: frozenset[str] = field(default_factory=lambda: frozenset({"customer"}))
    auth_source: str = "unknown"

    @property
    def is_authenticated(self) -> bool:
        return bool(self.user_id and self.user_id.strip())

    def has_role(self, role: str) -> bool:
        return role in self.roles


_current_security_context: ContextVar[SecurityContext | None] = ContextVar(
    "current_security_context",
    default=None,
)


def get_current_security_context(required: bool = True) -> SecurityContext | None:
    context = _current_security_context.get()
    if required and (context is None or not context.is_authenticated):
        raise PermissionError("Authenticated security context is required.")
    return context


@contextmanager
def bind_security_context(context: SecurityContext):
    token = _current_security_context.set(context)
    try:
        yield context
    finally:
        _current_security_context.reset(token)
