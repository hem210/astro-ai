"""
Auth routes — signup, login, refresh, logout.

Refresh token lifecycle:
  - Stored as SHA-256 hash in refresh_tokens table (raw token never persisted)
  - Set as HttpOnly; Secure; SameSite=Strict cookie named 'refresh_token'
  - On refresh: cookie is read, hashed, looked up in DB
  - On logout: token is marked revoked, cookie is cleared
"""

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.limiter import limiter
from app.core.auth import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.db.models import RefreshToken, User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"
_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds

# Secure cookies are dropped by browsers over plain HTTP — only require it when
# the frontend is actually served over HTTPS (e.g. in production).
_COOKIE_SECURE = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").startswith("https://")


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite="strict",
        max_age=_COOKIE_MAX_AGE,
        path="/auth/refresh",   # cookie is only sent to the refresh endpoint
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE, path="/auth/refresh")


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def signup(request: Request, body: SignupRequest, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.flush()  # get user.id before commit

    raw_refresh = generate_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=refresh_token_expiry(),
    ))
    db.commit()

    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    raw_refresh = generate_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=refresh_token_expiry(),
    ))
    db.commit()

    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
):
    invalid = HTTPException(status_code=401, detail="Invalid or expired refresh token")

    if not refresh_token:
        raise invalid

    token_record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_refresh_token(refresh_token)
    ).first()

    if not token_record:
        raise invalid
    if token_record.revoked:
        raise invalid
    if token_record.expires_at < datetime.now(timezone.utc):
        raise invalid

    # Rotate refresh token — revoke old, issue new
    token_record.revoked = True

    raw_refresh = generate_refresh_token()
    db.add(RefreshToken(
        user_id=token_record.user_id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=refresh_token_expiry(),
    ))
    db.commit()

    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=create_access_token(token_record.user_id))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
):
    if refresh_token:
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token_hash == hash_refresh_token(refresh_token)
        ).first()
        if token_record and not token_record.revoked:
            token_record.revoked = True
            db.commit()

    _clear_refresh_cookie(response)
