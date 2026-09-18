"""
PII Masking & Reversible Pseudonymization Module.

Protects sensitive employee emails and internal service account credentials
when communicating with external cloud LLMs (Groq / OpenAI).
Local models (Ollama) bypass this module to run directly on localhost.
"""

import re
from typing import Tuple, Dict

# Regex for standard RFC 5322 emails (including ceridian.com, dayforce.com, corpadds.com)
# Supports optional whitespace around '@' commonly found in Word tables or OCR scans
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
    re.IGNORECASE
)


# Regex for RPA Service Accounts:
# Matches patterns like G1RPAPROD01SVC, G8RPAService1, G4IPBOTAZURESVC, G4RPAQA01SVC, etc.
SVC_ACCOUNT_PATTERN = re.compile(
    r'\b(?:G\d+[A-Za-z0-9_]*(?:SVC|Service\d*)|[A-Z0-9_]+(?:RPAPROD|RPASERVICE|BOTAZURESVC|RPAQA\d*SVC))\b',
    re.IGNORECASE
)


class PIISanitizer:
    """
    Session-scoped reversible pseudonymizer for cloud LLM requests.
    Maintains a consistent mapping across context, query, and chat history.
    """

    def __init__(self):
        self.forward_vault: Dict[str, str] = {}
        self.email_counter = 0
        self.svc_counter = 0

    def mask(self, text: str) -> str:
        """Masks emails and service accounts in text using consistent tokens."""
        if not text:
            return text

        def mask_email(match: re.Match) -> str:
            raw = match.group(0)
            for stored_raw, token in self.forward_vault.items():
                if stored_raw.lower() == raw.lower():
                    return token

            self.email_counter += 1
            token = f"__EMAIL_{self.email_counter}__"
            self.forward_vault[raw] = token
            return token

        def mask_svc(match: re.Match) -> str:
            raw = match.group(0)
            for stored_raw, token in self.forward_vault.items():
                if stored_raw.lower() == raw.lower():
                    return token

            self.svc_counter += 1
            token = f"__SVC_ACCOUNT_{self.svc_counter}__"
            self.forward_vault[raw] = token
            return token

        sanitized = EMAIL_PATTERN.sub(mask_email, text)
        sanitized = SVC_ACCOUNT_PATTERN.sub(mask_svc, sanitized)
        return sanitized

    def restore(self, text: str) -> str:
        """Restores original values for all masked tokens in the text."""
        if not text or not self.forward_vault:
            return text

        reverse_vault = {token: raw for raw, token in self.forward_vault.items()}
        restored = text
        for token in sorted(reverse_vault.keys(), key=len, reverse=True):
            restored = restored.replace(token, reverse_vault[token])
        return restored

    @property
    def count(self) -> int:
        return len(self.forward_vault)

    @property
    def has_pii(self) -> bool:
        return len(self.forward_vault) > 0


def sanitize_pii(text: str) -> Tuple[str, Dict[str, str]]:
    """Convenience functional helper for single-string pseudonymization."""
    sanitizer = PIISanitizer()
    sanitized = sanitizer.mask(text)
    reverse_vault = {token: raw for raw, token in sanitizer.forward_vault.items()}
    return sanitized, reverse_vault


def restore_pii(text: str, reverse_vault: Dict[str, str]) -> str:
    """Convenience functional helper for single-string restoration."""
    if not text or not reverse_vault:
        return text
    restored = text
    for token in sorted(reverse_vault.keys(), key=len, reverse=True):
        restored = restored.replace(token, reverse_vault[token])
    return restored

