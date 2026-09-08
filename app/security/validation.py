import re

from app.config.settings import settings

_ORDER_RE = re.compile(r"^#?[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_GID_RE = re.compile(r"^gid://shopify/[A-Za-z]+/[A-Za-z0-9?=&._-]+$")


def validate_order_number(value: str) -> str:
    normalized = (value or "").strip()
    if normalized.lower().startswith("order "):
        normalized = normalized[6:].strip()
    if not normalized or not _ORDER_RE.fullmatch(normalized):
        raise ValueError("Invalid order number format.")
    return normalized


def validate_shopify_gid(value: str, field_name: str = "Shopify ID") -> str:
    normalized = (value or "").strip()
    if not normalized or len(normalized) > 512 or not _GID_RE.fullmatch(normalized):
        raise ValueError(f"Invalid {field_name} format.")
    return normalized


def validate_quantity(value: int, *, maximum: int | None = None) -> int:
    limit = maximum if maximum is not None else settings.max_cart_item_quantity
    if value < 1 or value > limit:
        raise ValueError(f"Quantity must be between 1 and {limit}.")
    return value


def extract_explicit_cart_quantity(message: str) -> int | None:
    """Extract an explicitly stated cart quantity without using an LLM.

    This is a security/business-rule pre-check, not full intent parsing. It
    intentionally focuses on strong quantity forms and avoids treating sizes
    such as "US 8" as cart quantity.
    """
    text = (message or "").strip()
    if not text:
        return None

    patterns = [
        # Add 2 Shoes / Add -2 Shoes / Add the 3 quantity of Shoes
        r"(?i)\badd\s+(?:the\s+)?(-?\d+)\b",
        # add quantity 3 / quantity of 3 / quantity to 3
        r"(?i)\bquantity\s*(?:of|=|to)?\s*(-?\d+)\b",
        # qty 3 / qty=3
        r"(?i)\bqty\s*(?:=|of|to)?\s*(-?\d+)\b",
        # 3 x Athletic Running Shoes (only when followed by x)
        r"(?i)\b(-?\d+)\s*x\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    return None


def validate_explicit_cart_quantity(message: str) -> int | None:
    quantity = extract_explicit_cart_quantity(message)
    if quantity is None:
        return None
    return validate_quantity(quantity)
