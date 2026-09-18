"""
Structured logging module for Dayforce Automation Atlas with secret sanitization.
"""

import logging
import re
import sys

# Regex pattern to match potential secrets in string outputs
SECRET_PATTERN = re.compile(
    r"(sk-[a-zA-Z0-9_\-]{20,}|password[=:]\s*\S+|key[=:]\s*\S+|postgresql://\S+)",
    re.IGNORECASE,
)


class SecretSanitizingFormatter(logging.Formatter):
    """Logging formatter that redacts detected secrets and sensitive patterns."""

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return SECRET_PATTERN.sub("[REDACTED_SECRET]", formatted)


def setup_logger(name: str = "atlas", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a structured, secret-safe logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = SecretSanitizingFormatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logger()
