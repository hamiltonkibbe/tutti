#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

import os


from typing import NamedTuple, TypedDict


class RedisSemaphoreHandle(NamedTuple):
    name: str
    identifier: str


class RedisConnectionInfo(TypedDict):
    host: str
    port: int
    db: int


def get_redis_connection_info() -> RedisConnectionInfo:
    return {
        "host": os.getenv("TUTTI_REDIS_HOST", "localhost"),
        "port": int(os.getenv("TUTTI_REDIS_PORT", 6379)),
        "db": int(os.getenv("TUTTI_REDIS_DB", 0)),
    }
