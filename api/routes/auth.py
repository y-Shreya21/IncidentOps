"""
Authentication API Endpoints for AI IncidentOps.
Supports login, JWT token issuance, and user session inspection.
"""

from __future__ import annotations

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from security.auth import (
    SEED_USERS,
    UserAuth,
    create_access_token,
    get_current_user,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str
    expires_in_minutes: int


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    user = SEED_USERS.get(request.username)
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token(
        data={"sub": user["username"], "username": user["username"], "role": user["role"]},
        expires_delta=timedelta(hours=24),
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=user["username"],
        role=user["role"],
        expires_in_minutes=1440,
    )


@router.get("/me", response_model=UserAuth)
def get_me(current_user: UserAuth = Depends(get_current_user)):
    return current_user
