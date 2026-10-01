"""
PII Sanitizer & Data Scrubber.
Treats complaint text as untrusted and strips out sensitive PII before any LLM processing.
Masks email addresses, phone numbers, credit card numbers, and SSNs.
"""

import re

def sanitize_pii(text: str) -> str:
    """Mask personal data (phone, card, email, SSN) before passing to agents/LLM."""
    if not text:
        return ""

    sanitized = text

    # Credit card numbers (13 to 19 digits with optional hyphens/spaces)
    sanitized = re.sub(
        r'\b(?:\d[ -]*?){13,19}\b',
        '[REDACTED_CARD]',
        sanitized
    )

    # Email addresses
    sanitized = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b',
        '[REDACTED_EMAIL]',
        sanitized
    )

    # Phone numbers (various domestic and international formats)
    sanitized = re.sub(
        r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        '[REDACTED_PHONE]',
        sanitized
    )

    # Social security numbers
    sanitized = re.sub(
        r'\b\d{3}-\d{2}-\d{4}\b',
        '[REDACTED_SSN]',
        sanitized
    )

    return sanitized
