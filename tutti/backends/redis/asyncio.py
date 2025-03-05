#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

"""Redis distributed synchronization primitive backend"""

import logging

from redis.asyncio import Redis
from redis.asyncio.lock import Lock as RedisLock

from tutti.base import AsyncLockABC, AsyncSemaphoreABC, TUTTI_LOGGER_NAME

from .connection import get_async_redis
from .utils import (
    aacquire_lock,
    arelease_lock,
    aacquire_semaphore,
    arelease_semaphore,
    alocked,
)
from .types import RedisSemaphoreHandle


logger = logging.getLogger(TUTTI_LOGGER_NAME)


class RedisWrapper:
    @staticmethod
    async def acquire_lock(
        conn: Redis,
        lock_name: str,
        blocking: bool = True,
        timeout: float | None = None
    ) -> tuple[RedisLock, bool]:
        return await aacquire_lock(conn, lock_name, blocking, timeout)

    @staticmethod
    async def release_lock(conn: Redis, lock: RedisLock) -> bool:
        return await arelease_lock(conn, lock)

    @staticmethod
    async def locked(conn: Redis, lock_name: str) -> bool:
        return await alocked(conn, lock_name)

    @staticmethod
    async def acquire_semaphore(
        conn: Redis,
        lock_name: str,
        value: int = 1,
        blocking: bool = True,
        timeout: float = -1
    ) -> RedisSemaphoreHandle | None:
        return await aacquire_semaphore(
            conn, lock_name, value, blocking, timeout
        )

    @staticmethod
    async def release_semaphore(conn: Redis, lock: RedisSemaphoreHandle) -> bool:
        return await arelease_semaphore(conn, lock)


class Lock(AsyncLockABC):

    def __init__(
        self,
        lock_name: str,
        connection_url: str,
        blocking: bool = True,
        timeout: float | None = None,
        conn: Redis | None = None,
        redis_wrapper: type[RedisWrapper] = RedisWrapper
    ) -> None:
        self._handle: RedisLock | None = None
        self._blocking = blocking
        self._timeout = timeout
        self._lock_name = lock_name
        self._redis_wrapper = redis_wrapper

        if conn is not None and isinstance(conn, Redis):
            self._conn = conn
        else:
            self._conn = get_async_redis(connection_url)

    async def acquire(self, blocking: bool = True, timeout: float | None = None) -> bool:
        try:
            lock, result = await self._redis_wrapper.acquire_lock(
                self._conn,
                lock_name=self._lock_name,
                blocking=blocking,
                timeout=self._get_timeout(timeout)
            )
        except Exception as e:
            logger.error(f"Error acquiring redis lock: {e}")
            self._handle = None
            return False
        else:
            if result:
                self._handle = lock
            return result

    async def release(self) -> None:
        if self._handle is None:
            raise RuntimeError("Attempt to release unlocked lock.")
        await self._redis_wrapper.release_lock(self._conn, self._handle)

    async def locked(self) -> bool:
        return await self._redis_wrapper.locked(self._conn, self._lock_name)

    async def __aenter__(self) -> "Lock":
        acquired = await self.acquire(self._blocking, self._timeout)
        if not acquired:
            raise RuntimeError("Unable to acquire lock")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return await self.release()

    def _get_timeout(self, timeout: float | None = None) -> float | None:
        return self._timeout if self._timeout is not None else timeout


class Semaphore(AsyncSemaphoreABC):
    def __init__(
        self,
        lock_name: str,
        value: int,
        timeout: float,
        connection_url: str,
        conn: Redis | None = None,
        redis_wrapper: type[RedisWrapper] = RedisWrapper
    ) -> None:
        self._lock_name = lock_name
        self._value = value
        self._timeout = timeout
        self._handle: RedisSemaphoreHandle | None = None
        self._redis_wrapper = redis_wrapper
        self._connection_url = connection_url

        if conn is not None and isinstance(conn, Redis):
            self._conn = conn
        else:
            self._conn = get_async_redis(connection_url)

    async def acquire(
        self,
        blocking: bool = True,
        timeout: float | None = None
    ) -> bool:
        timeout_float = self._get_timeout(timeout)
        lock_name = f"{self._lock_name}-lock"
        async with Lock(
            lock_name=lock_name,
            connection_url=self._connection_url,
            blocking=blocking,
            timeout=timeout_float,
            conn=self._conn,
            redis_wrapper=self._redis_wrapper
        ):
            try:
                self._handle = await self._redis_wrapper.acquire_semaphore(
                    self._conn,
                    value=self._value,
                    lock_name=self._lock_name,
                    blocking=blocking,
                    timeout=timeout_float
                )
            except Exception as e:
                logger.error(f"Error acquiring tutti semaphore: {e}")
                self._handle = None
                return False
            else:
                return self._handle is not None

    async def release(self, n: int = 1) -> None:
        if self._handle is not None:
            await self._redis_wrapper.release_semaphore(self._conn, self._handle)

    async def __aenter__(self) -> "Semaphore":
        acquired = await self.acquire()
        if not acquired:
            raise RuntimeError("Unable to acquire semaphore")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._handle:
            return await self.release()

    def _get_timeout(self, timeout: float | None = None) -> float:
        return self._timeout if self._timeout is not None else timeout if timeout is not None else -1


class BoundedSemaphore(Semaphore):
    async def release(self, n: int = 1) -> None:
        if self._handle is None or not await self._redis_wrapper.release_semaphore(self._conn, self._handle):
            raise ValueError("Semaphore released too many times")


__all__ = ["Lock", "Semaphore", "BoundedSemaphore"]
