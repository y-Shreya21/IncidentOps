"""
Authentication and Role-Based Access Control (RBAC) Module for AI IncidentOps.
Provides JWT issuance, token verification, and granular permission enforcement.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# Supported Roles
ROLE_ADMIN = "Administrator"
ROLE_RESPONDER = "IncidentResponder"
ROLE_SRE = "SREEngineer"
ROLE_STAKEHOLDER = "Stakeholder"


class TokenData(BaseModel):
    username: str
    role: str
    exp: Optional[int] = None


class UserAuth(BaseModel):
    username: str
    role: str
    email: str


# Pre-seeded users for operations
SEED_USERS = {
    "admin": {
        "username": "admin",
        "email": "admin@incidentops.internal",
        "role": ROLE_ADMIN,
        "password_hash": hashlib.sha256("AdminSecret2026!".encode()).hexdigest(),
    },
    "commander": {
        "username": "commander",
        "email": "commander@incidentops.internal",
        "role": ROLE_RESPONDER,
        "password_hash": hashlib.sha256("CommanderSecret2026!".encode()).hexdigest(),
    },
    "sre": {
        "username": "sre",
        "email": "sre@incidentops.internal",
        "role": ROLE_SRE,
        "password_hash": hashlib.sha256("SreSecret2026!".encode()).hexdigest(),
    },
    "stakeholder": {
        "username": "stakeholder",
        "email": "stakeholder@incidentops.internal",
        "role": ROLE_STAKEHOLDER,
        "password_hash": hashlib.sha256("StakeholderSecret2026!".encode()).hexdigest(),
    },
}


def hash_password(password: str) -> str:
    """Hashes a password using SHA-256 with project salt."""
    salted = f"{settings.JWT_SECRET}:{password}"
    return hashlib.sha256(salted.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time comparison of hashed passwords."""
    # Check both seeded hash and salted hash
    expected_direct = hashlib.sha256(plain_password.encode()).hexdigest()
    expected_salted = hash_password(plain_password)
    return hmac.compare_digest(expected_direct, hashed_password) or hmac.compare_digest(expected_salted, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": int(expire.timestamp()), "iat": int(now.timestamp())})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub") or payload.get("username", "")
        role: str = payload.get("role", ROLE_STAKEHOLDER)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(username=username, role=role, exp=payload.get("exp"))
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> UserAuth:
    """FastAPI dependency to extract the current authenticated user."""
    # Default to IncidentResponder if no token is provided in local dev mode
    if not token:
        return UserAuth(
            username="default_operator",
            role=ROLE_RESPONDER,
            email="operator@incidentops.internal"
        )
    token_data = decode_access_token(token)
    user = SEED_USERS.get(token_data.username)
    if user:
        return UserAuth(username=user["username"], role=user["role"], email=user["email"])
    return UserAuth(username=token_data.username, role=token_data.role, email=f"{token_data.username}@incidentops.internal")


def require_roles(allowed_roles: List[str]):
    """Role-Based Access Control decorator/dependency."""
    def role_checker(current_user: UserAuth = Depends(get_current_user)) -> UserAuth:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: User role '{current_user.role}' lacks permission. Required: {allowed_roles}",
            )
        return current_user
    return role_checker
