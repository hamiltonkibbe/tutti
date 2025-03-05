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
    """Lock congfiguration Base class.

    Parameters:
        name (str):
            The name of the Redis Lock.
        timeout (float):
            The timeout for acquiring the lock, in seconds
        blocking (bool):
            Whether to block while waiting for the lock to be released.
        connection_url (str):
            The Redis connection URL.
        blocking (bool):
            Whether to block while waiting for the lock to be released. Defaults to `True`.
    """
    connection_url: str


@dataclass
class RedisSemaphoreConfig(SemaphoreConfig):
    """Configuration for Redis semaphores.

    Parameters:
        name (str):
            The name of the Semaphore.
        max_concurrency (int):
            The maximum number of concurrent accesses to the resource.
        connection_url (str):
            The Redis connection URL.
        lock_timeout (float):
            The timeout for acquiring the lock, in seconds
        lock_blocking (bool):
            Whether to block while waiting for the lock to be released. Defaults to `True`.
    """
    connection_url: str
    lock_timeout: float
