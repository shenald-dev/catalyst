"""Cache Plugin: Redis/Memcached wrapper with hit/miss metrics.

Supports Redis (redis-py) and in-memory fallback.
Configuration:
  - backend: "redis" or "memory"
  - host: Redis host (default localhost)
  - port: Redis port (default 6379)
  - db: Redis DB number (default 0)
"""
import asyncio
from typing import Any, Optional
from core.plugin import Plugin

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class CachePlugin(Plugin):
    name = "cache"
    version = "0.2.0"
    description = "Cache layer with Redis or in-memory backend"

    def __init__(self, backend: str = "memory", host: str = "localhost",
                 port: int = 6379, db: int = 0, namespace: str = "catalyst"):
        """
        Args:
            backend: "redis" or "memory"
            host, port, db: Redis connection settings
            namespace: Key prefix
        """
        self.backend = backend.lower()
        self.host = host
        self.port = port
        self.db = db
        self.namespace = namespace
        self._client = None
        self._local_cache = {}  # simple dict for memory backend
        self._stats = {"hits": 0, "misses": 0, "sets": 0}

    def on_load(self) -> None:
        pass

    async def on_unload(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    def health_check(self) -> bool:
        if self.backend == "redis":
            return HAS_REDIS
        return True

    async def execute(self, action: str, key: str, value: Any = None,
                      ttl: Optional[int] = None) -> Any:
        """
        Cache operations.

        Args:
            action: "get", "set", "delete", "exists"
            key: Cache key (namespaced automatically)
            value: Value to store (for set)
            ttl: Time-to-live in seconds

        Returns:
            Value (for get), boolean (for exists/set), or None.
        """
        full_key = f"{self.namespace}:{key}"

        if action == "get":
            result = await self._get(full_key)
            return result
        elif action == "set":
            await self._set(full_key, value, ttl)
            return True
        elif action == "delete":
            return await self._delete(full_key)
        elif action == "exists":
            return await self._exists(full_key)
        else:
            raise ValueError(f"Unknown cache action: {action}")

    async def _get(self, key: str) -> Any:
        if self.backend == "memory":
            if key in self._local_cache:
                self._stats["hits"] += 1
                return self._local_cache[key]
            else:
                self._stats["misses"] += 1
                return None
        elif self.backend == "redis":
            if not HAS_REDIS:
                raise RuntimeError("redis-py is not installed")
            if self._client is None:
                await self._connect_redis()
            val = await self._client.get(key)
            if val is not None:
                self._stats["hits"] += 1
                return val
            else:
                self._stats["misses"] += 1
                return None
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    async def _set(self, key: str, value: Any, ttl: Optional[int]) -> None:
        if self.backend == "memory":
            self._local_cache[key] = value
            self._stats["sets"] += 1
        elif self.backend == "redis":
            if not HAS_REDIS:
                raise RuntimeError("redis-py is not installed")
            if self._client is None:
                await self._connect_redis()
            await self._client.set(key, value, ex=ttl)
            self._stats["sets"] += 1

    async def _delete(self, key: str) -> bool:
        if self.backend == "memory":
            if key in self._local_cache:
                del self._local_cache[key]
                return True
            return False
        elif self.backend == "redis":
            if self._client is None:
                await self._connect_redis()
            result = await self._client.delete(key)
            return result > 0
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    async def _exists(self, key: str) -> bool:
        val = await self._get(key)
        return val is not None

    async def _connect_redis(self) -> None:
        if not HAS_REDIS:
            raise RuntimeError("redis-py is not installed")
        self._client = aioredis.Redis(host=self.host, port=self.port, db=self.db)

    def metrics(self) -> Dict[str, int]:
        return self._stats.copy()