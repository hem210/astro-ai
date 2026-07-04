from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.auth import decode_access_token


def get_user_key(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            user_id = decode_access_token(auth.removeprefix("Bearer "))
            return str(user_id)
        except (JWTError, Exception):
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=get_remote_address)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down."},
    )
