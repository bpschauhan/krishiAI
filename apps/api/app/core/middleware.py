import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

import redis
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.security import verify_clerk_jwt

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class AuthenticationStateMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
            try:
                request.state.auth_claims = verify_clerk_jwt(token)
            except Exception as exc:  # noqa: BLE001
                request.state.auth_error = exc
        return await call_next(request)


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method not in UNSAFE_METHODS or not request.url.path.startswith("/api/v1"):
            return await call_next(request)

        if request.headers.get("authorization", "").lower().startswith("bearer "):
            return await call_next(request)

        has_cookie_session = "__session" in request.cookies or "__client" in request.cookies
        if not has_cookie_session:
            return await call_next(request)

        origin = request.headers.get("origin")
        if origin and origin not in settings.csrf_trusted_origins:
            return Response("Untrusted request origin", status_code=status.HTTP_403_FORBIDDEN)

        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("x-csrf-token")
        if not csrf_cookie or csrf_cookie != csrf_header:
            return Response("Invalid CSRF token", status_code=status.HTTP_403_FORBIDDEN)

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._memory_buckets: dict[str, deque[float]] = defaultdict(deque)
        self._redis_client = None
        if settings.RATE_LIMIT_ENABLED:
            try:
                self._redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            except redis.RedisError:
                self._redis_client = None

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if not settings.RATE_LIMIT_ENABLED or request.url.path.startswith(("/health", "/version")):
            return await call_next(request)

        key = self._key_for_request(request)
        if self._is_limited(key):
            return Response("Rate limit exceeded", status_code=status.HTTP_429_TOO_MANY_REQUESTS)

        return await call_next(request)

    def _key_for_request(self, request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = forwarded_for.split(",", 1)[0].strip() if forwarded_for else request.client.host if request.client else "unknown"
        auth_sub = getattr(getattr(request.state, "auth_claims", None), "subject", None)
        identity = auth_sub or client_ip
        return f"rate:{identity}:{request.url.path}"

    def _is_limited(self, key: str) -> bool:
        if self._redis_client is not None:
            try:
                count = self._redis_client.incr(key)
                if count == 1:
                    self._redis_client.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS)
                return int(count) > settings.RATE_LIMIT_REQUESTS
            except redis.RedisError:
                self._redis_client = None

        now = time.time()
        bucket = self._memory_buckets[key]
        while bucket and now - bucket[0] > settings.RATE_LIMIT_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= settings.RATE_LIMIT_REQUESTS:
            return True
        bucket.append(now)
        return False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response
