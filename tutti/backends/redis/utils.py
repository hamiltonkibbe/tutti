#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

import asyncio
import time
import uuid

from redis import Redis
from redis.lock import Lock as RedisLock
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio.lock import Lock as AsyncRedisLock

from .types import RedisSemaphoreHandle


def acquire_lock(
    conn: Redis,
    lock_name: str,
    blocking: bool = True,
    timeout: float | None = None
) -> tuple[RedisLock, bool]:
    lock = conn.lock(
        lock_name,
        timeout=timeout,
        blocking_timeout=None if not blocking else timeout
    )
    result = lock.acquire()
    return lock, result


async def aacquire_lock(
    conn: AsyncRedis,
    lock_name: str,
    blocking: bool = True,
    timeout: float | None = None
) -> tuple[AsyncRedisLock, bool]:
    lock = conn.lock(
        lock_name,
        timeout=timeout,
        blocking_timeout=None if not blocking else timeout
    )
    result = await lock.acquire()
    return lock, result


def release_lock(conn: Redis, lock: RedisLock) -> bool:
    lock.release()
    return True


async def arelease_lock(conn: AsyncRedis, lock: AsyncRedisLock) -> bool:
    await lock.release()
    return True


def acquire_semaphore(
    conn: Redis,
    lock_name: str,
    value: int = 1,
    blocking: bool = True,
    timeout: float = -1
) -> RedisSemaphoreHandle | None:

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
        counter = pipeline.execute()[-1]
        pipeline.zadd(lock_name, {identifier: now})
        pipeline.zadd(czset, {identifier: counter})
        pipeline.zrank(czset, identifier)
        result = pipeline.execute()
        if result[-1] < value:
            return RedisSemaphoreHandle(lock_name, identifier)
        pipeline.zrem(lock_name, identifier)
        pipeline.zrem(czset, identifier)
        pipeline.execute()

        if (not blocking) or (timeout >= 0 and time.time() > (now + timeout)):
            return None
        time.sleep(0.001)


async def aacquire_semaphore(
    conn: AsyncRedis,
    lock_name: str,
    value: int = 1,
    blocking: bool = True,
    timeout: float = -1
) -> RedisSemaphoreHandle | None:

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
        await asyncio.sleep(0.001)


def release_semaphore(conn: Redis, lock: RedisSemaphoreHandle) -> bool:
    pipeline = conn.pipeline(transaction=True)
    pipeline.zrem(lock.name, lock.identifier)
    pipeline.zrem(f"{lock.name}-owner", lock.identifier)
    result = pipeline.execute()
    return bool(result[0])


async def arelease_semaphore(conn: AsyncRedis, lock: RedisSemaphoreHandle) -> bool:
    pipeline = conn.pipeline(transaction=True)
    pipeline.zrem(lock.name, lock.identifier)
    pipeline.zrem(f"{lock.name}-owner", lock.identifier)
    result = await pipeline.execute()
    return bool(result[0])


def locked(conn: Redis, lock_name: str) -> bool:
    lock = conn.lock(lock_name)
    return lock.locked()


async def alocked(conn: AsyncRedis, lock_name: str) -> bool:
    lock = conn.lock(lock_name)
    return await lock.locked()
