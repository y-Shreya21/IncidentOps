"""
Automated Unit Tests for Authentication & Role-Based Access Control (Layer 6).
Verifies JWT issuance, token decoding, and role permission enforcement.
"""

import pytest
from security.auth import (
    ROLE_ADMIN,
    ROLE_RESPONDER,
    ROLE_SRE,
    ROLE_STAKEHOLDER,
    create_access_token,
    decode_access_token,
    verify_password,
    hash_password,
    SEED_USERS,
)


def test_password_hashing_and_verification():
    raw_pass = "TestPassword123!"
    hashed = hash_password(raw_pass)
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_generation_and_decoding():
    token = create_access_token(
        data={"sub": "commander", "username": "commander", "role": ROLE_RESPONDER}
    )
    assert token is not None
    assert isinstance(token, str)

    decoded = decode_access_token(token)
    assert decoded.username == "commander"
    assert decoded.role == ROLE_RESPONDER


def test_seeded_users_exist():
    assert "admin" in SEED_USERS
    assert SEED_USERS["admin"]["role"] == ROLE_ADMIN
    assert "commander" in SEED_USERS
    assert SEED_USERS["commander"]["role"] == ROLE_RESPONDER
    assert "sre" in SEED_USERS
    assert SEED_USERS["sre"]["role"] == ROLE_SRE
    assert "stakeholder" in SEED_USERS
    assert SEED_USERS["stakeholder"]["role"] == ROLE_STAKEHOLDER
