import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import FastAPI

from app.core.config import Settings, get_settings


class ConnectionManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.postgres_pool: Optional[Any] = None
        self.mongo_client: Optional[Any] = None
        self.mongo_database: Optional[Any] = None
        self.redis_client: Optional[Any] = None
        self.milvus_client: Optional[Any] = None
        self.milvus_alias = "default"
        self.statuses: Dict[str, Dict[str, Any]] = {
            "postgres": {"configured": bool(settings.postgres_host), "connected": False},
            "mongodb": {"configured": bool(settings.mongo_host), "connected": False},
            "redis": {"configured": bool(settings.redis_host), "connected": False},
            "milvus": {"configured": bool(settings.milvus_host), "connected": False},
        }

    async def connect(self) -> None:
        await asyncio.gather(
            self._connect_postgres(),
            self._connect_mongo(),
            self._connect_redis(),
            self._connect_milvus(),
        )

    async def close(self) -> None:
        if self.postgres_pool is not None:
            await self.postgres_pool.close()
        if self.mongo_client is not None:
            self.mongo_client.close()
        if self.redis_client is not None:
            await self.redis_client.aclose()
        if self.milvus_client is not None:
            await asyncio.to_thread(self._disconnect_milvus)

    async def _connect_postgres(self) -> None:
        if not self.settings.postgres_host:
            return
        try:
            import asyncpg

            self.postgres_pool = await asyncpg.create_pool(
                host=self.settings.postgres_host,
                port=self.settings.postgres_port,
                user=self.settings.postgres_user,
                password=self.settings.postgres_password,
                database=self.settings.postgres_database,
                min_size=self.settings.postgres_min_pool_size,
                max_size=self.settings.postgres_max_pool_size,
                timeout=self.settings.connection_timeout_seconds,
            )
            async with self.postgres_pool.acquire() as connection:
                await connection.execute("select 1")
            self._mark_connected("postgres", {"database": self.settings.postgres_database})
        except Exception as exc:
            self._mark_failed("postgres", exc)

    async def _connect_mongo(self) -> None:
        if not self.settings.mongo_host:
            return
        try:
            from motor.motor_asyncio import AsyncIOMotorClient

            self.mongo_client = AsyncIOMotorClient(
                host=self.settings.mongo_host,
                port=self.settings.mongo_port,
                username=self.settings.mongo_user or None,
                password=self.settings.mongo_password or None,
                authSource=self.settings.mongo_auth_source,
                serverSelectionTimeoutMS=int(self.settings.connection_timeout_seconds * 1000),
            )
            await self.mongo_client.admin.command("ping")
            self.mongo_database = self.mongo_client[self.settings.mongo_database]
            self._mark_connected("mongodb", {"database": self.settings.mongo_database})
        except Exception as exc:
            self._mark_failed("mongodb", exc)

    async def _connect_redis(self) -> None:
        if not self.settings.redis_host:
            return
        try:
            from redis.asyncio import Redis

            self.redis_client = Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_database,
                username=self.settings.redis_user or None,
                password=self.settings.redis_password or None,
                socket_connect_timeout=self.settings.connection_timeout_seconds,
                socket_timeout=self.settings.connection_timeout_seconds,
                decode_responses=True,
            )
            await self.redis_client.ping()
            self._mark_connected("redis")
        except Exception as exc:
            self._mark_failed("redis", exc)

    async def _connect_milvus(self) -> None:
        if not self.settings.milvus_host:
            return
        try:
            from pymilvus import connections, utility

            kwargs = {
                "alias": self.milvus_alias,
                "host": self.settings.milvus_host,
                "port": str(self.settings.milvus_port),
                "secure": self.settings.milvus_secure,
            }
            if self.settings.milvus_token:
                kwargs["token"] = self.settings.milvus_token
            if self.settings.milvus_database:
                kwargs["db_name"] = self.settings.milvus_database
            await asyncio.to_thread(connections.connect, **kwargs)
            await asyncio.to_thread(utility.list_collections, using=self.milvus_alias)
            self.milvus_client = connections
            details = {"database": self.settings.milvus_database} if self.settings.milvus_database else None
            self._mark_connected("milvus", details)
        except Exception as exc:
            self._mark_failed("milvus", exc)

    def _disconnect_milvus(self) -> None:
        from pymilvus import connections

        connections.disconnect(self.milvus_alias)

    def dependency_status(self) -> Dict[str, Dict[str, Any]]:
        return self.statuses

    def _mark_connected(self, name: str, details: Optional[Dict[str, Any]] = None) -> None:
        status = {"configured": True, "connected": True}
        if details:
            status.update(details)
        self.statuses[name] = status

    def _mark_failed(self, name: str, exc: Exception) -> None:
        self.statuses[name] = {
            "configured": True,
            "connected": False,
            "error": f"{exc.__class__.__name__}: {exc}",
        }


connection_manager = ConnectionManager(get_settings())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await connection_manager.connect()
    app.state.connections = connection_manager
    try:
        yield
    finally:
        await connection_manager.close()
