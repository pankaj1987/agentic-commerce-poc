from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from typing import Any


SENSITIVE_KEYS = {
    "authorization",
    "x-shopify-access-token",
    "x-shopify-storefront-access-token",
    "shopify_access_token",
    "shopify_storefront_token",
    "access_token",
    "api_key",
    "langsmith_api_key",
    "cart_id",
    "checkouturl",
    "checkout_url",
    "phone",
    "address",
    "shipping_address",
}

_EMAIL_RE = re.compile(r"(?P<local>[A-Za-z0-9._%+-]+)@(?P<domain>[A-Za-z0-9.-]+\.[A-Za-z]{2,})")
_TOKEN_PATTERNS = [
    re.compile(r"(?i)(shpat_[A-Za-z0-9_-]+)"),
    re.compile(r"(?i)(Bearer\s+[A-Za-z0-9._~+\-/=]+)"),
    re.compile(r"(?i)(X-Shopify-(?:Storefront-)?Access-Token\s*[:=]\s*)[^\s,]+"),
]


def mask_email(value: str) -> str:
    match = _EMAIL_RE.fullmatch(value.strip())
    if not match:
        return "[REDACTED_EMAIL]"
    local = match.group("local")
    domain = match.group("domain")
    first = local[:1] or "*"
    return f"{first}***@{domain}"


def redact_text(value: str) -> str:
    text = value
    text = _EMAIL_RE.sub(lambda m: f"{m.group('local')[:1]}***@{m.group('domain')}", text)
    for pattern in _TOKEN_PATTERNS:
        if pattern.groups == 1:
            text = pattern.sub("[REDACTED_TOKEN]", text)
        else:
            text = pattern.sub(r"\1[REDACTED]", text)
    # Shopify opaque cart IDs include a key query parameter. Never log it.
    text = re.sub(r"gid://shopify/Cart/[^\s'\"]+", "[REDACTED_CART_ID]", text)
    return text


def redact_mapping(value: Any) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).lower()
            if normalized in SENSITIVE_KEYS or "token" in normalized or "secret" in normalized:
                result[str(key)] = "[REDACTED]"
            elif normalized == "email" and isinstance(item, str):
                result[str(key)] = mask_email(item)
            else:
                result[str(key)] = redact_mapping(item)
        return result
    if isinstance(value, list):
        return [redact_mapping(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_mapping(item) for item in value)
    if isinstance(value, str):
        return redact_text(value)
    return value


class SensitiveDataFilter(logging.Filter):
    """Best-effort final logging boundary.

    Application code should still avoid logging secrets in the first place;
    this filter provides an additional central safety net.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = redact_text(record.msg)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = redact_mapping(record.args)
                elif isinstance(record.args, tuple):
                    record.args = tuple(redact_mapping(arg) for arg in record.args)
        except Exception:
            # Logging redaction must never break request processing.
            pass
        return True


def install_sensitive_data_filter() -> None:
    root = logging.getLogger()
    for handler in root.handlers:
        if not any(isinstance(f, SensitiveDataFilter) for f in handler.filters):
            handler.addFilter(SensitiveDataFilter())
