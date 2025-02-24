#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

"""Redis distributed synchronization primitive backend"""

import time
from asyncio import sleep
from typing import Optional

import uuid

from redis.asyncio import Redis
from redis.asyncio.lock import Lock as RedisLock

from tutti.base import AsyncLockABC, AsyncSemaphoreABC
from tutti.utils import get_redis_connection_info, RedisSemaphoreHandle


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
    except:
        return None


async def __release_lock(conn: Redis, lock: RedisLock) -> bool:
    await lock.release()
    return True


async def __acquire_semaphore(
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
        counter = await pipeline.execute()[-1]
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


async def __release_semaphore(conn: Redis, lock: RedisSemaphoreHandle) -> bool:
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
    ) -> None:
        self._conn = Redis(**get_redis_connection_info())
        self._handle: Optional[RedisLock] = None
        self._blocking = blocking
        self._timeout = timeout
        self._lock_name = lock_name

    async def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        lock = self._conn.lock(self._lock_name, timeout=None, blocking_timeout=timeout)
        try:
            result = await lock.acquire()
            if result:
                self._handle = lock
            return result
        except:
            self._handle = None
            return False

    async def release(self) -> None:
        if self._handle is None:
            raise RuntimeError("Attempt to release unlocked lock.")
        await __release_lock(self._conn, self._handle)

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


class Semaphore(AsyncSemaphoreABC):
    def __init__(self, lock_name: str, value: int = 1):
        self._conn = Redis(**get_redis_connection_info())
        self._value = value
        self._handle: Optional[RedisSemaphoreHandle] = None
        self._lock_name = lock_name

    async def acquire(
        self,
        blocking: bool = True,
        timeout: Optional[float] = None
    ) -> bool:
        timeout_float = -1 if timeout is None else timeout
        lock_name = f"{self._lock_name}-lock"
        async with Lock(lock_name, blocking, timeout):
            self._handle = await __acquire_semaphore(
                self._conn,
                value=self._value,
                lock_name=self._lock_name,
                blocking=blocking,
                timeout=timeout_float
            )
            return self._handle is not None

    async def release(self, n: int = 1) -> None:
        if self._handle is not None:
            await __release_semaphore(self._conn, self._handle)

    async def __aenter__(self) -> "Semaphore":
        acquired = await self.acquire()
        if not acquired:
            raise RuntimeError("Unable to acquire semaphore")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._handle:
            return await self.release()


class BoundedSemaphore(Semaphore):
    async def release(self, n: int = 1) -> None:
        if self._handle is None or not  await __release_semaphore(self._conn, self._handle):
            raise ValueError("Semaphore released too many times")



__all__ = ["Lock", "Semaphore", "BoundedSemaphore"]
