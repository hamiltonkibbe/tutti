#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

"""Redis distributed synchronization primitive backend"""

import time
from typing import Optional

import logging
import uuid

from redis import Redis
from redis.lock import Lock as RedisLock

from tutti.base import LockABC, SemaphoreABC, TUTTI_LOGGER_NAME

from .utils import get_redis_connection_info
from .types import RedisSemaphoreHandle


logger = logging.getLogger(TUTTI_LOGGER_NAME)


def acquire_lock(
    conn: Redis,
    lock_name: str,
    blocking: bool = True,
    timeout: float = -1
) -> Optional[RedisLock]:
    lock_name = f"tutti-{lock_name}"
    lock = conn.lock(lock_name, timeout=None, blocking_timeout=None if not blocking else timeout)
    try:
        lock.acquire()
        return lock
    except Exception as e:
        logger.error(f"Error acquiring tutti lock: {e}", exc_info=True)
        return None


def release_lock(conn: Redis, lock: RedisLock) -> bool:
    lock.release()
    return True


def acquire_semaphore(
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


def release_semaphore(conn: Redis, lock: RedisSemaphoreHandle) -> bool:
    pipeline = conn.pipeline(transaction=True)
    pipeline.zrem(lock.name, lock.identifier)
    pipeline.zrem(f"{lock.name}-owner", lock.identifier)
    result = pipeline.execute()
    return bool(result[0])


class Lock(LockABC):

    def __init__(self, lock_name: str, timeout: float, blocking: bool = True) -> None:
        self._conn = Redis(**get_redis_connection_info())
        self._handle: Optional[RedisLock] = None
        self._blocking = blocking
        self._timeout = timeout
        self._lock_name = lock_name

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        lock = self._conn.lock(self._lock_name, timeout=None, blocking_timeout=timeout)
        try:
            result = lock.acquire()
            if result:
                self._handle = lock
            return result
        except Exception as e:
            logger.error(f"Error acquiring tutti lock: {e}", exc_info=True)
            self._handle = None
            return False

    def release(self) -> None:
        if self._handle is None:
            raise RuntimeError("Attempt to release unlocked lock.")
        release_lock(self._conn, self._handle)

    def locked(self) -> bool:
        lock = self._conn.lock(self._lock_name)
        return lock.locked()

    def __enter__(self) -> "Lock":
        acquired = self.acquire(self._blocking, self._timeout)
        if not acquired:
            raise RuntimeError("Unable to acquire lock")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return self.release()


class Semaphore(SemaphoreABC):
    def __init__(self, lock_name: str, value: int, timeout: float):
        self._conn = Redis(**get_redis_connection_info())
        self._value = value
        self._handle: Optional[RedisSemaphoreHandle] = None
        self._lock_name = lock_name
        self._timeout = timeout

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        with Lock(
            lock_name=f"{self._lock_name}-lock",
            blocking=blocking,
            timeout=self._timeout
        ):
            self._handle = acquire_semaphore(
                self._conn,
                value=self._value, 
                lock_name=self._lock_name,
                blocking=blocking,
                timeout=self._timeout
            )
            return self._handle is not None

    def release(self, n: int = 1) -> None:
        if self._handle is not None:
            release_semaphore(self._conn, self._handle)

    def __enter__(self) -> "Semaphore":
        acquired = self.acquire()
        if not acquired:
            raise RuntimeError("Unable to acquire semaphore")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._handle:
            return self.release()


class BoundedSemaphore(Semaphore):
    def release(self, n: int = 1) -> None:
        if self._handle is None or not release_semaphore(self._conn, self._handle):
            raise ValueError("Semaphore released too many times")


__all__ = ["Lock", "Semaphore", "BoundedSemaphore"]
