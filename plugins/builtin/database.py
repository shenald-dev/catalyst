"""Database Plugin: Execute SQL with connection pooling.

Supports SQLite (aiosqlite) and PostgreSQL (asyncpg).
Configuration:
  - driver: "sqlite" or "postgres"
  - database: path (sqlite) or connection string (postgres)
  - pool_size: number of connections (default 5)
"""
import asyncio
from typing import Any, Dict, Optional
from core.plugin import Plugin

try:
    import aiosqlite
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False

try:
    import asyncpg
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False


class DatabasePlugin(Plugin):
    name = "database"
    version = "0.2.0"
    description = "SQL execution with connection pooling (SQLite/PostgreSQL)"

    def __init__(self, driver: str = "sqlite", database: str = ":memory:",
                 pool_size: int = 5, **kwargs):
        """
        Args:
            driver: "sqlite" or "postgres"
            database: SQLite file path or PostgreSQL connection string
            pool_size: Connection pool size
        """
        self.driver = driver.lower()
        self.database = database
        self.pool_size = pool_size
        self._pool = None
        self._stats = {"hits": 0, "misses": 0, "errors": 0}

    def on_load(self) -> None:
        # No I/O here; pool created on first use
        pass

    async def on_unload(self) -> None:
        if self._pool:
            if self.driver == "sqlite":
                await self._pool.close()
            elif self.driver == "postgres":
                await self._pool.close()
            self._pool = None

    def health_check(self) -> bool:
        if self.driver == "sqlite" and not HAS_SQLITE:
            return False
        if self.driver == "postgres" and not HAS_POSTGRES:
            return False
        return True

    async def execute(self, query: str, params: tuple = (), fetch: bool = False) -> Any:
        """
        Execute a SQL query.

        Args:
            query: SQL statement
            params: Query parameters
            fetch: If True, return rows (SELECT); else return rowcount

        Returns:
            Fetched rows (list of dicts) or row count.
        """
        if self._pool is None:
            await self._ensure_pool()

        try:
            if self.driver == "sqlite":
                async with self._pool.acquire() as conn:
                    async with conn.execute(query, params) as cursor:
                        if fetch:
                            rows = await cursor.fetchall()
                            self._stats["hits"] += 1
                            return [dict(row) for row in rows]
                        else:
                            self._stats["hits"] += 1
                            return cursor.rowcount
            elif self.driver == "postgres":
                async with self._pool.acquire() as conn:
                    if fetch:
                        rows = await conn.fetch(query, *params)
                        self._stats["hits"] += 1
                        return [dict(row) for row in rows]
                    else:
                        result = await conn.execute(query, *params)
                        self._stats["hits"] += 1
                        return result
            else:
                raise ValueError(f"Unsupported driver: {self.driver}")
        except Exception as e:
            self._stats["errors"] += 1
            raise

    async def _ensure_pool(self) -> None:
        if self.driver == "sqlite":
            if not HAS_SQLITE:
                raise RuntimeError("aiosqlite is not installed")
            self._pool = await aiosqlite.create_pool(
                database=self.database,
                size=self.pool_size
            )
        elif self.driver == "postgres":
            if not HAS_POSTGRES:
                raise RuntimeError("asyncpg is not installed")
            self._pool = await asyncpg.create_pool(
                dsn=self.database,
                min_size=self.pool_size,
                max_size=self.pool_size
            )
        else:
            raise ValueError(f"Unsupported driver: {self.driver}")

    def metrics(self) -> Dict[str, int]:
        """Return plugin metrics (hits, misses, errors)."""
        return self._stats.copy()