#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>
#

import multiprocessing
import time

from colorama import Fore, Style

from tutti import Lock, Semaphore
from tutti.configuration import RedisLockConfig, RedisSemaphoreConfig


CONNNECTION_URL = "redis://localhost:6379/0"

REDIS_LOCK_CONFIG = RedisLockConfig(
    connection_url=CONNNECTION_URL,
    name="demo-lock",
    timeout=5,
    blocking=True,
)

REDIS_SEMAPHORE_CONFIG = RedisSemaphoreConfig(
    connection_url=CONNNECTION_URL,
    max_concurrency=2,
    name="demo-semaphore",
    lock_timeout=5,
)


def pprint(data, process_id):
    color = [Fore.CYAN, Fore.MAGENTA, Fore.YELLOW, Fore.GREEN, Fore.BLUE, Fore.RED][process_id]
    print(f"{color}    {data}{Style.RESET_ALL}")


def use_protected_resource():
    # Just pretend...
    time.sleep(0.3)


def access_exclusive_resource(process_id: int) -> None:
    """Use a distributed lock to limit access to a critical resource"""

    with Lock(REDIS_LOCK_CONFIG):
        pprint(f"Process {process_id} Entering critical section", process_id)
        use_protected_resource()
        pprint(f"Process {process_id} Leaving critical section", process_id)


def access_limited_resource(process_id: int) -> None:
    """Use a distributed semaphore to limit access to a critical resource"""

    with Semaphore(REDIS_SEMAPHORE_CONFIG):
        pprint(f"Process {process_id} Entering critical section", process_id)
        use_protected_resource()
        pprint(f"Process {process_id} Leaving critical section", process_id)


if __name__ == "__main__":
    # Run
    with multiprocessing.Pool(4) as p:
        print("\n============================================================================")
        print("Lock demo: Only one process may be in the critical section at a time")
        print("============================================================================")
        p.map(access_exclusive_resource, range(4))

        print("\n============================================================================")
        print("Semaphore demo: Up to two processes may be in the critical section at a time")
        print("============================================================================")
        p.map(access_limited_resource, range(4))
