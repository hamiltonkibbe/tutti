#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

"""Redis distributed synchronization primitive backend"""

import logging

from redis import Redis
from redis.lock import Lock as RedisLock

from tutti.base import LockABC, SemaphoreABC, TUTTI_LOGGER_NAME

from .connection import get_sync_redis
from .utils import (
    acquire_lock,
    release_lock,
    acquire_semaphore,
    release_semaphore,
    locked,
)
from .types import RedisSemaphoreHandle


logger = logging.getLogger(TUTTI_LOGGER_NAME)


class RedisWrapper:
    @staticmethod
    def acquire_lock(
        conn: Redis,
        lock_name: str,
        blocking: bool = True,
        timeout: float | None = None
    ) -> tuple[RedisLock, bool]:
        return acquire_lock(conn, lock_name, blocking, timeout)

    @staticmethod
    def release_lock(conn: Redis, lock: RedisLock) -> bool:
        return release_lock(conn, lock)

    @staticmethod
    def locked(conn: Redis, lock_name: str) -> bool:
        return locked(conn, lock_name)

    @staticmethod
    def acquire_semaphore(
        conn: Redis,
        lock_name: str,
        value: int = 1,
        blocking: bool = True,
        timeout: float = -1
    ) -> RedisSemaphoreHandle | None:
        return acquire_semaphore(conn, lock_name, value, blocking, timeout)

    @staticmethod
    def release_semaphore(conn: Redis, lock: RedisSemaphoreHandle) -> bool:
        return release_semaphore(conn, lock)


class Lock(LockABC):

    def __init__(
        self,
        lock_name: str,
        connection_url: str,
        timeout: float,
        blocking: bool = True,
        conn: Redis | None = None,
        redis_wrapper: type[RedisWrapper] = RedisWrapper
    ) -> None:
        self._handle: RedisLock | None = None
        self._blocking = blocking
        self._timeout = timeout
        self._lock_name = lock_name
        self._connection_url = connection_url
        self._redis_wrapper = redis_wrapper

        if conn is not None and isinstance(conn, Redis):
            self._conn = conn
        else:
            self._conn = get_sync_redis(connection_url)

    def acquire(self, blocking: bool = True, timeout: float | None = None) -> bool:
        try:
            lock, result = self._redis_wrapper.acquire_lock(
                self._conn,
                lock_name=self._lock_name,
                blocking=blocking,
                timeout=self._get_timeout(timeout)
            )
        except Exception as e:
            logger.error(f"Error acquiring tutti lock: {e}", exc_info=True)
            self._handle = None
            return False
        else:
            if result:
                self._handle = lock
            return result

    def release(self) -> None:
        if self._handle is None:
            raise RuntimeError("Attempt to release unlocked lock.")
        self._redis_wrapper.release_lock(self._conn, self._handle)

    def locked(self) -> bool:
        return self._redis_wrapper.locked(self._conn, self._lock_name)

    def __enter__(self) -> "Lock":
        acquired = self.acquire(self._blocking, self._timeout)
        if not acquired:
            raise RuntimeError("Unable to acquire lock")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return self.release()

    def _get_timeout(self, timeout: float | None = None) -> float | None:
        return self._timeout if self._timeout is not None else timeout


class Semaphore(SemaphoreABC):
    def __init__(
        self,
        lock_name: str,
        value: int,
        timeout: float,
        connection_url: str,
        conn: Redis | None = None,
        redis_wrapper: type[RedisWrapper] = RedisWrapper
    ) -> None:
        self._value = value
        self._handle: RedisSemaphoreHandle | None = None
        self._lock_name = lock_name
        self._timeout = timeout
        self._connection_url = connection_url
        self._redis_wrapper = redis_wrapper

        if conn is not None and isinstance(conn, Redis):
            self._conn = conn
        else:
            self._conn = get_sync_redis(connection_url)

    def acquire(self, blocking: bool = True, timeout: float | None = None) -> bool:
        timeout_float = self._get_timeout(timeout)
        lock_name = f"{self._lock_name}-lock"
        with Lock(
            lock_name=lock_name,
            blocking=blocking,
            connection_url=self._connection_url,
            timeout=timeout_float,
            conn=self._conn,
            redis_wrapper=self._redis_wrapper
        ):
            self._handle = self._redis_wrapper.acquire_semaphore(
                self._conn,
                value=self._value,
                lock_name=self._lock_name,
                blocking=blocking,
                timeout=self._timeout
            )
            return self._handle is not None

    def release(self, n: int = 1) -> None:
        if self._handle is not None:
            self._redis_wrapper.release_semaphore(self._conn, self._handle)

    def __enter__(self) -> "Semaphore":
        acquired = self.acquire()
        if not acquired:
            raise RuntimeError("Unable to acquire semaphore")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._handle:
            return self.release()

    def _get_timeout(self, timeout: float | None = None) -> float:
        return self._timeout if self._timeout is not None else timeout if timeout is not None else -1


class BoundedSemaphore(Semaphore):
    def release(self, n: int = 1) -> None:
        if self._handle is None or not self._redis_wrapper.release_semaphore(self._conn, self._handle):
            raise ValueError("Semaphore released too many times")


__all__ = ["Lock", "Semaphore", "BoundedSemaphore"]
