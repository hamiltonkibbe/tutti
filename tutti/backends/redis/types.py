#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

from tutti.base import LockConfig, SemaphoreConfig

from dataclasses import dataclass
from typing import NamedTuple


class RedisSemaphoreHandle(NamedTuple):
    name: str
    identifier: str


@dataclass
class RedisLockConfig(LockConfig):
    connection_url: str
    name: str
    timeout: float
    blocking: bool = True


@dataclass
class RedisSemaphoreConfig(SemaphoreConfig):
    connection_url: str
    max_concurrency: int
    lock: RedisLockConfig
