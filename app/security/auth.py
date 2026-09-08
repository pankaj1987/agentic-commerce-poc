from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.config.settings import settings
from app.persistence.repositories.customer_identity_repository import CustomerIdentityRepository
from app.security.context import SecurityContext


def _parse_roles(raw: str | None) -> frozenset[str]:
    roles = {role.strip().lower() for role in (raw or "customer").split(",") if role.strip()}
    return frozenset(roles or {"customer"})


def get_security_context(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_shopify_customer_id: str | None = Header(default=None, alias="X-Shopify-Customer-Id"),
    x_user_roles: str | None = Header(default=None, alias="X-User-Roles"),
) -> SecurityContext:
    """Resolve authenticated identity.

    `dev_header` exists only for this local POC and emulates a trusted identity
    gateway. Production must replace it with verified OIDC/JWT authentication;
    clients must never be allowed to self-assert user/customer IDs.
    """

    if settings.auth_mode != "dev_header":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Configured authentication mode is not implemented in this POC.",
        )

    user_id = (x_user_id or settings.dev_user_id or "").strip()
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")

    mapping = CustomerIdentityRepository.get_by_user_id(user_id)

    asserted_customer_id = (x_shopify_customer_id or settings.dev_shopify_customer_id or "").strip() or None
    if mapping and asserted_customer_id and mapping.shopify_customer_id != asserted_customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user/customer mapping does not match the stored identity.",
        )

    if mapping is None and asserted_customer_id:
        mapping = CustomerIdentityRepository.upsert_mapping(
            user_id=user_id,
            shopify_customer_id=asserted_customer_id,
        )

    return SecurityContext(
        user_id=user_id,
        shopify_customer_id=mapping.shopify_customer_id if mapping else None,
        roles=_parse_roles(x_user_roles or settings.dev_user_roles),
        auth_source="dev_header",
    )
