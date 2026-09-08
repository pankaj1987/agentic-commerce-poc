from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class GuardrailDecision(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"


@dataclass(frozen=True)
class GuardrailResult:
    decision: GuardrailDecision
    reason: str | None = None

    @property
    def allowed(self) -> bool:
        return self.decision == GuardrailDecision.ALLOW


class InputGuardrail:
    """Deterministic first-line guardrail for clearly malicious requests.

    This is intentionally conservative: it blocks requests attempting to
    exfiltrate secrets/system instructions or explicitly override controls.
    Normal commerce questions containing words such as "ignore" are not
    blocked unless combined with a sensitive target.
    """

    MAX_MESSAGE_LENGTH = 10_000

    _patterns = [
        re.compile(r"(?is)ignore\s+(all\s+)?(previous|prior|system|developer)\s+instructions?.*(token|secret|password|api\s*key|system\s*prompt)"),
        re.compile(r"(?is)(show|reveal|print|return|give)\s+(me\s+)?(your\s+)?(system\s*prompt|developer\s*message|api\s*key|access\s*token|shopify\s*token|secret)"),
        re.compile(r"(?is)(bypass|disable|override)\s+(the\s+)?(guardrail|authorization|security|policy|tool\s+restriction)"),
        re.compile(r"(?is)call\s+(any\s+)?tool.*(without|bypass).*(authorization|permission|confirmation)"),
        # Strong SQL/injection syntax. This is deliberately narrow so normal
        # commerce language containing words such as "or" is not blocked.
        re.compile(r"(?is)[\"']\s*(or|and)\s+[\"']?\d+[\"']?\s*=\s*[\"']?\d+[\"']?"),
        re.compile(r"(?is)(--|/\*|\*/|;\s*(select|insert|update|delete|drop|alter)\b)"),
    ]

    @classmethod
    def validate_message(cls, message: str) -> GuardrailResult:
        normalized = (message or "").strip()
        if not normalized:
            return GuardrailResult(GuardrailDecision.BLOCK, "Message cannot be empty.")
        if len(normalized) > cls.MAX_MESSAGE_LENGTH:
            return GuardrailResult(
                GuardrailDecision.BLOCK,
                f"Message exceeds the maximum length of {cls.MAX_MESSAGE_LENGTH} characters.",
            )
        if "\x00" in normalized:
            return GuardrailResult(GuardrailDecision.BLOCK, "Message contains invalid control characters.")
        for pattern in cls._patterns:
            if pattern.search(normalized):
                return GuardrailResult(
                    GuardrailDecision.BLOCK,
                    "The request attempts to override security controls or access sensitive system information.",
                )
        return GuardrailResult(GuardrailDecision.ALLOW)
