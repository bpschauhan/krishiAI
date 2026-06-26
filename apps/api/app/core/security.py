from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient

from app.core.config import settings


@dataclass(frozen=True)
class ClerkClaims:
    subject: str
    payload: dict[str, Any]


@lru_cache(maxsize=1)
def _get_jwks_client() -> PyJWKClient:
    jwks_url = settings.clerk_jwks_url
    if not jwks_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk JWKS URL is not configured",
        )
    return PyJWKClient(jwks_url)


def verify_clerk_jwt(token: str) -> ClerkClaims:
    if not settings.CLERK_ISSUER_URL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk issuer is not configured",
        )

    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.CLERK_ISSUER_URL,
            audience=settings.CLERK_JWT_AUDIENCE,
            options={"verify_aud": bool(settings.CLERK_JWT_AUDIENCE)},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return ClerkClaims(subject=subject, payload=payload)
