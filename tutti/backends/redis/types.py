#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

from dataclasses import dataclass
from typing import NamedTuple

from tutti.base import LockConfig, SemaphoreConfig


class RedisSemaphoreHandle(NamedTuple):
    name: str
    identifier: str


@dataclass
class RedisLockConfig(LockConfig):
    """Configuration for Redis locks.

    Parameters:
        connection_url (str):
            The Redis connection URL.
        name (str):
            The name of the Redis Lock.
        timeout (float):
            The timeout for acquiring the lock, in seconds
        blocking (bool):
            Whether to block while waiting for the lock to be released. Defaults to `True`.
    """
    connection_url: str
    name: str
    timeout: float
    blocking: bool = True


@dataclass
class RedisSemaphoreConfig(SemaphoreConfig):
    """Configuration for Redis semaphores.

    Parameters:
        connection_url (str):
            The Redis connection URL.
        max_concurrency (int):
            The maximum number of concurrent accesses to the resource.
        lock (RedisLockConfig):
            The configuration object for the lock used by the semaphore. A lock
            is required for the redis semaphore implementation.
    """
    connection_url: str
    max_concurrency: int
    lock: RedisLockConfig
