#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

"""Redis distributed synchronization primitive backend"""

import os
import time
from typing import NamedTuple, Optional

import uuid

from redis import Redis
from redis.lock import Lock as RedisLock

from tutti.base import LockABC, SemaphoreABC
from tutti.utils import get_name_from_caller


class RedisSemaphoreHandle(NamedTuple):
    name: str
    identifier: str


def acquire_lock(
        conn: Redis,
        lock_name: Optional[str] = None,
        blocking: bool = True,
        timeout: float = -1
) -> Optional[RedisLock]:
    lock_name = f"tutti-{lock_name if lock_name is not None else get_name_from_caller()}"
    lock = conn.lock(lock_name, timeout=None, blocking_timeout=None if not blocking else timeout)
    try:
        lock.acquire()
        return lock
    except:
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

def _get_conn_info():
    return {
        "host": os.getenv("TUTTI_REDIS_HOST", "localhost"),
        "port": int(os.getenv("TUTTI_REDIS_PORT", 6379)),
        "db": int(os.getenv("TUTTI_REDIS_DB", 0))
    }

class Lock(LockABC):

    def __init__(self, blocking: bool = True, timeout: Optional[float] = None, lock_name: Optional[str] = None) -> None:
        self._conn = Redis(**_get_conn_info())
        self._handle: Optional[RedisLock] = None
        self._blocking = blocking
        self._timeout = timeout
        self._lock_name = lock_name if lock_name is not None else get_name_from_caller()

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        lock = self._conn.lock(self._lock_name, timeout=None, blocking_timeout=timeout)
        try:
            result = lock.acquire()
            if result:
                self._handle = lock
            return result
        except:
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
    def __init__(self, value: int = 1, lock_name: Optional[str] = None):
        self._conn = Redis(**_get_conn_info())
        self._value = value
        self._handle: Optional[RedisSemaphoreHandle] = None
        self._lock_name = lock_name if lock_name is not None else get_name_from_caller()

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        timeout_float = -1 if timeout is None else timeout
        with Lock(blocking, timeout, lock_name=f"{self._lock_name}-lock"):
            self._handle = acquire_semaphore(self._conn, value=self._value, lock_name=self._lock_name, blocking=blocking, timeout=timeout_float)
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
