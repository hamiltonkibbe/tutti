#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

"""Redis distributed synchronization primitive backend"""

import time
from asyncio import sleep
from typing import Optional

import logging
import uuid

from redis.asyncio import Redis
from redis.asyncio.lock import Lock as RedisLock

from tutti.base import AsyncLockABC, AsyncSemaphoreABC, TUTTI_LOGGER_NAME

from .utils import get_redis_connection_info
from .types import RedisSemaphoreHandle


logger = logging.getLogger(TUTTI_LOGGER_NAME)


async def acquire_lock(
    conn: Redis,
    lock_name: str,
    blocking: bool = True,
    timeout: float = -1
) -> RedisLock | None:
    lock_name = f"tutti-{lock_name}"
    lock = conn.lock(lock_name, timeout=None, blocking_timeout=None if not blocking else timeout)
    try:
        await lock.acquire()
        return lock
    except Exception as e:
        logger.error(f"Error acquiring tutti lock: {e}", exc_info=True)
        return None


async def release_lock(conn: Redis, lock: RedisLock) -> bool:
    await lock.release()
    return True


async def acquire_semaphore(
    conn: Redis,
    lock_name: str,
    value: int = 1,
    blocking: bool = True,
    timeout: float = -1
) -> Optional[RedisSemaphoreHandle]:

    identifier = str(uuid.uuid4())
    czset = f"{lock_name}-owner"
    ctr = f"{lock_name}-counter"

    now = time.time()

    while True:
        pipeline = conn.pipeline(transaction=True)

        if timeout >= 0:
            pipeline.zremrangebyscore(lock_name, "-inf", now - timeout)

        pipeline.zinterstore(czset, {czset: 1, lock_name: 0})
        pipeline.incr(ctr)
        counter_coroutine = await pipeline.execute()
        counter = counter_coroutine[-1]
        pipeline.zadd(lock_name, {identifier: now})
        pipeline.zadd(czset, {identifier: counter})
        pipeline.zrank(czset, identifier)
        result = await pipeline.execute()
        if result[-1] < value:
            return RedisSemaphoreHandle(lock_name, identifier)
        pipeline.zrem(lock_name, identifier)
        pipeline.zrem(czset, identifier)
        await pipeline.execute()

        if (not blocking) or (timeout >= 0 and time.time() > (now + timeout)):
            return None
        await sleep(0.001)


async def release_semaphore(conn: Redis, lock: RedisSemaphoreHandle) -> bool:
    pipeline = conn.pipeline(transaction=True)
    pipeline.zrem(lock.name, lock.identifier)
    pipeline.zrem(f"{lock.name}-owner", lock.identifier)
    result = await pipeline.execute()
    return bool(result[0])


class Lock(AsyncLockABC):

    def __init__(
        self,
        lock_name: str,
        blocking: bool = True,
        timeout: Optional[float] = None,
        conn: Optional[Redis] = None
    ) -> None:
        self._conn = conn if conn is not None else Redis(**get_redis_connection_info())
        self._handle: Optional[RedisLock] = None
        self._blocking = blocking
        self._timeout = timeout
        self._lock_name = lock_name

    async def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        lock = self._conn.lock(self._lock_name, timeout=timeout, blocking_timeout=timeout)
        try:
            result = await lock.acquire(blocking=blocking, blocking_timeout=timeout)
            if result:
                self._handle = lock
            return result
        except Exception as e:
            logger.error(f"Error acquiring redis lock: {e}")
            self._handle = None
            return False

    async def release(self) -> None:
        if self._handle is None:
            raise RuntimeError("Attempt to release unlocked lock.")
        await release_lock(self._conn, self._handle)

    async def locked(self) -> bool:
        lock = self._conn.lock(self._lock_name)
        return await lock.locked()

    async def __aenter__(self) -> "Lock":
        acquired = await self.acquire(self._blocking, self._timeout)
        if not acquired:
            raise RuntimeError("Unable to acquire lock")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return await self.release()

    def _get_timeout(self, timeout: Optional[float] = None) -> Optional[float]:
        return self._timeout if self._timeout is not None else timeout


class Semaphore(AsyncSemaphoreABC):
    def __init__(self, lock_name: str, value: int, timeout: float) -> None:
        self._conn = Redis(**get_redis_connection_info())
        self._lock_name = lock_name
        self._value = value
        self._timeout = timeout
        self._handle: Optional[RedisSemaphoreHandle] = None

    async def acquire(
        self,
        blocking: bool = True,
        timeout: Optional[float] = None
    ) -> bool:
        timeout_float = self._get_timeout(timeout)
        lock_name = f"{self._lock_name}-lock"
        async with Lock(lock_name, blocking, timeout_float, self._conn):
            try:
                self._handle = await acquire_semaphore(
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
            return self._handle is not None

    async def release(self, n: int = 1) -> None:
        if self._handle is not None:
            await release_semaphore(self._conn, self._handle)

    async def __aenter__(self) -> "Semaphore":
        acquired = await self.acquire()
        if not acquired:
            raise RuntimeError("Unable to acquire semaphore")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._handle:
            return await self.release()

    def _get_timeout(self, timeout: Optional[float] = None) -> float:
        return self._timeout if self._timeout is not None else timeout if timeout is not None else -1


class BoundedSemaphore(Semaphore):
    async def release(self, n: int = 1) -> None:
        if self._handle is None or not  await release_semaphore(self._conn, self._handle):
            raise ValueError("Semaphore released too many times")


__all__ = ["Lock", "Semaphore", "BoundedSemaphore"]
