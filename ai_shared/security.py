"""
Security — PII detection, content filtering, and input validation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ── PII Detection ────────────────────────────────────────────────────────────

class PIIType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    PASSPORT = "passport"
    CUSTOM = "custom"


@dataclass
class PIIMatch:
    pii_type: PIIType
    text: str
    start: int
    end: int


_DEFAULT_PATTERNS: dict[PIIType, re.Pattern[str]] = {
    PIIType.EMAIL: re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    PIIType.PHONE: re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b"),
    PIIType.SSN: re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    PIIType.CREDIT_CARD: re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    PIIType.IP_ADDRESS: re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
}


class PIIDetector:
    """Detect and redact PII from text."""

    def __init__(
        self,
        *,
        enabled_types: set[PIIType] | None = None,
        custom_patterns: dict[str, re.Pattern[str]] | None = None,
        redaction_char: str = "█",
    ) -> None:
        self.redaction_char = redaction_char
        self._patterns: dict[str, re.Pattern[str]] = {}
        types = enabled_types or set(_DEFAULT_PATTERNS.keys())
        for t in types:
            if t in _DEFAULT_PATTERNS:
                self._patterns[t.value] = _DEFAULT_PATTERNS[t]
        if custom_patterns:
            self._patterns.update(custom_patterns)

    def detect(self, text: str) -> list[PIIMatch]:
        matches: list[PIIMatch] = []
        for name, pattern in self._patterns.items():
            for m in pattern.finditer(text):
                try:
                    pii_type = PIIType(name)
                except ValueError:
                    pii_type = PIIType.CUSTOM
                matches.append(PIIMatch(pii_type=pii_type, text=m.group(), start=m.start(), end=m.end()))
        return matches

    def redact(self, text: str) -> str:
        matches = self.detect(text)
        if not matches:
            return text
        # Sort by start position in reverse so indices stay valid
        matches.sort(key=lambda m: m.start, reverse=True)
        result = text
        for m in matches:
            replacement = self.redaction_char * len(m.text)
            result = result[:m.start] + replacement + result[m.end:]
        return result

    def has_pii(self, text: str) -> bool:
        return len(self.detect(text)) > 0


# ── Content Filtering ────────────────────────────────────────────────────────

class ContentCategory(str, Enum):
    HARMFUL = "harmful"
    HATEFUL = "hateful"
    SEXUAL = "sexual"
    VIOLENCE = "violence"
    SELF_HARM = "self_harm"
    ILLEGAL = "illegal"
    PROMPT_INJECTION = "prompt_injection"


@dataclass
class FilterResult:
    is_safe: bool
    flagged_categories: list[ContentCategory] = field(default_factory=list)
    confidence: float = 1.0
    details: str = ""


# Common prompt-injection indicators
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(your\s+)?instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:DAN|a\s+new)", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\|(?:im_start|im_end|system|endoftext)\|>", re.IGNORECASE),
]


class ContentFilter:
    """Rule-based content safety filter."""

    def __init__(
        self,
        *,
        blocked_categories: set[ContentCategory] | None = None,
        custom_blocklist: list[str] | None = None,
        check_injection: bool = True,
    ) -> None:
        self.blocked_categories = blocked_categories or {ContentCategory.PROMPT_INJECTION}
        self.check_injection = check_injection
        self._blocklist = [w.lower() for w in (custom_blocklist or [])]

    def check(self, text: str) -> FilterResult:
        flagged: list[ContentCategory] = []

        # Prompt injection detection
        if self.check_injection and ContentCategory.PROMPT_INJECTION in self.blocked_categories:
            for pattern in _INJECTION_PATTERNS:
                if pattern.search(text):
                    flagged.append(ContentCategory.PROMPT_INJECTION)
                    break

        # Custom blocklist
        lower = text.lower()
        for word in self._blocklist:
            if word in lower:
                flagged.append(ContentCategory.HARMFUL)
                break

        return FilterResult(
            is_safe=len(flagged) == 0,
            flagged_categories=flagged,
            confidence=0.9 if flagged else 1.0,
        )


# ── Input Validation ─────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    sanitized: str = ""


class InputValidator:
    """Validate and sanitize user inputs before sending to LLMs."""

    def __init__(
        self,
        *,
        max_length: int = 100_000,
        min_length: int = 1,
        strip_html: bool = True,
        strip_control_chars: bool = True,
    ) -> None:
        self.max_length = max_length
        self.min_length = min_length
        self.strip_html = strip_html
        self.strip_control_chars = strip_control_chars

    def validate(self, text: str) -> ValidationResult:
        errors: list[str] = []
        sanitized = text

        if self.strip_control_chars:
            sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", sanitized)

        if self.strip_html:
            sanitized = re.sub(r"<[^>]+>", "", sanitized)

        sanitized = sanitized.strip()

        if len(sanitized) < self.min_length:
            errors.append(f"Input too short (min {self.min_length} chars)")

        if len(sanitized) > self.max_length:
            errors.append(f"Input too long (max {self.max_length} chars)")
            sanitized = sanitized[: self.max_length]

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, sanitized=sanitized)
