from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import redis

from app.core.config import settings


@dataclass
class MemoryCacheEntry:
    expires_at: float
    value: dict[str, Any]


class WeatherCache:
    def __init__(self, ttl_seconds: int = 900) -> None:
        self.ttl_seconds = ttl_seconds
        self._memory: dict[str, MemoryCacheEntry] = {}
        self._redis_client = None
        try:
            self._redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        except redis.RedisError:
            self._redis_client = None

    def get_json(self, key: str) -> dict[str, Any] | None:
        if self._redis_client is not None:
            try:
                raw_value = self._redis_client.get(key)
                return json.loads(raw_value) if raw_value else None
            except (redis.RedisError, json.JSONDecodeError):
                self._redis_client = None

        entry = self._memory.get(key)
        if entry is None:
            return None
        if entry.expires_at <= time.time():
            self._memory.pop(key, None)
            return None
        return entry.value

    def set_json(self, key: str, value: dict[str, Any]) -> None:
        if self._redis_client is not None:
            try:
                self._redis_client.setex(key, self.ttl_seconds, json.dumps(value))
                return
            except redis.RedisError:
                self._redis_client = None

        self._memory[key] = MemoryCacheEntry(expires_at=time.time() + self.ttl_seconds, value=value)

    def clear(self) -> None:
        self._memory.clear()


weather_cache = WeatherCache()
