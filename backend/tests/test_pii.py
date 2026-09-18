"""
Unit tests for PII Sanitization and Reversible Pseudonymization.
"""

import time
import pytest
from app.core.pii import sanitize_pii, restore_pii


def test_sanitize_emails():
    text = "Please reach out to Akhilesh.chamoli@ceridian.com or backup rafia.bokhari@ceridian.com."
    sanitized, vault = sanitize_pii(text)

    assert "Akhilesh.chamoli@ceridian.com" not in sanitized
    assert "rafia.bokhari@ceridian.com" not in sanitized
    assert "__EMAIL_1__" in sanitized
    assert "__EMAIL_2__" in sanitized
    assert len(vault) == 2

    # Roundtrip restore
    restored = restore_pii(sanitized, vault)
    assert restored == text


def test_sanitize_service_accounts():
    text = "The job runs under G1RPAPROD17SVC on machine 01 and G8RPAService1 on machine 02."
    sanitized, vault = sanitize_pii(text)

    assert "G1RPAPROD17SVC" not in sanitized
    assert "G8RPAService1" not in sanitized
    assert "__SVC_ACCOUNT_1__" in sanitized
    assert "__SVC_ACCOUNT_2__" in sanitized
    assert len(vault) == 2

    # Roundtrip restore
    restored = restore_pii(sanitized, vault)
    assert restored == text


def test_sanitize_email_with_service_account_prefix():
    # If a service account is used in an email address (e.g. G8RPAService1@corpadds.com)
    # it must be masked as a single email token rather than splitting into __SVC_ACCOUNT_X__@corpadds.com
    text = "Notification sent to G8RPAService1@corpadds.com from prod bot."
    sanitized, vault = sanitize_pii(text)

    assert "G8RPAService1@corpadds.com" not in sanitized
    assert "__EMAIL_1__" in sanitized
    assert "@corpadds.com" not in sanitized

    restored = restore_pii(sanitized, vault)
    assert restored == text


def test_repeated_entities_reuse_same_token():
    text = "Contact Alice.Li@dayforce.com. If Alice.Li@dayforce.com is OOO, ping G1RPAPROD01SVC or G1RPAPROD01SVC."
    sanitized, vault = sanitize_pii(text)

    assert sanitized.count("__EMAIL_1__") == 2
    assert sanitized.count("__SVC_ACCOUNT_1__") == 2
    assert len(vault) == 2

    restored = restore_pii(sanitized, vault)
    assert restored == text


def test_empty_and_null_safety():
    assert sanitize_pii("") == ("", {})
    assert sanitize_pii(None) == (None, {})
    assert restore_pii("", {}) == ""
    assert restore_pii("Hello world", {}) == "Hello world"


def test_pii_speed_benchmark():
    sample = """
    Server: OHA5RPAU1APP01.CORPADDS.COM
    Owner: Vishal.Saha@ceridian.com, Co-Owner: saikiran.cp@dayforce.com
    Service Account: G1RPAPROD22SVC and backup G8RPAService2@corpadds.com
    Escalation: ABharath.Rao@ceridian.com
    """ * 20  # ~4,000 characters

    t0 = time.perf_counter()
    sanitized, vault = sanitize_pii(sample)
    t_mask = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    restored = restore_pii(sanitized, vault)
    t_restore = (time.perf_counter() - t1) * 1000

    assert restored == sample
    # Must complete in under 5 milliseconds (normally < 0.2ms)
    assert (t_mask + t_restore) < 5.0


def test_pii_sanitizer_session():
    from app.core.pii import PIISanitizer

    sanitizer = PIISanitizer()
    context = "Lead contact: Vishal.Saha@ceridian.com. Service account: G1RPAPROD01SVC."
    query = "Who is Vishal.Saha@ceridian.com?"

    masked_ctx = sanitizer.mask(context)
    masked_query = sanitizer.mask(query)

    # Tokens must match between context and query
    assert "__EMAIL_1__" in masked_ctx
    assert "__EMAIL_1__" in masked_query
    assert "Vishal.Saha@ceridian.com" not in masked_ctx
    assert "Vishal.Saha@ceridian.com" not in masked_query

    # Simulated LLM response with tokens
    llm_reply = "The lead contact is __EMAIL_1__ and the process runs as __SVC_ACCOUNT_1__."
    restored_reply = sanitizer.restore(llm_reply)

    assert "Vishal.Saha@ceridian.com" in restored_reply
    assert "G1RPAPROD01SVC" in restored_reply
    assert "__EMAIL_1__" not in restored_reply
    assert "__SVC_ACCOUNT_1__" not in restored_reply

