#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>
#
import asyncio

from colorama import Fore, Style

from tutti.configuration import RedisLockConfig, RedisSemaphoreConfig
from tutti.asyncio import Lock, Semaphore


CONNNECTION_URL = "redis://localhost:6379/0"

REDIS_LOCK_CONFIG = RedisLockConfig(
    connection_url=CONNNECTION_URL,
    name="demo-lock",
    timeout=5,
)

REDIS_SEMAPHORE_CONFIG = RedisSemaphoreConfig(
    connection_url=CONNNECTION_URL,
    max_concurrency=2,
    name="demo-semaphore",
    lock_timeout=5,
)


def pprint(data, task_number):
    color = [Fore.CYAN, Fore.MAGENTA, Fore.YELLOW, Fore.GREEN, Fore.BLUE, Fore.RED][task_number]
    print(f"{color}    {data}{Style.RESET_ALL}")


async def use_protected_resource():
    # Just pretend...
    await asyncio.sleep(0.3)


async def access_exclusive_resource(task_number: int) -> None:
    """Use a distributed lock to limit access to a critical resource"""

    async with Lock(REDIS_LOCK_CONFIG):
        pprint(f"Task {task_number} Entering critical section", task_number)
        await use_protected_resource()
        pprint(f"Task {task_number} Leaving critical section", task_number)


async def access_limited_resource(task_number: int) -> None:
    """Use a distributed semaphore to limit access to a critical resource"""

    async with Semaphore(REDIS_SEMAPHORE_CONFIG):
        pprint(f"Task {task_number} Entering critical section", task_number)
        await use_protected_resource()
        pprint(f"Task {task_number} Leaving critical section", task_number)


async def main():
    print("\n============================================================================")
    print("Lock demo: Only one task may be in the critical section at a time")
    print("============================================================================")
    lock_tasks = [
        asyncio.create_task(access_exclusive_resource(i)) for i in range(4)
    ]
    await asyncio.gather(*lock_tasks)

    print("\n============================================================================")
    print("Semaphore demo: Up to two tasks may be in the critical section at a time")
    print("============================================================================")
    semaphore_tasks = [
        asyncio.create_task(access_limited_resource(i)) for i in range(4)
    ]
    await asyncio.gather(*semaphore_tasks)


if __name__ == "__main__":
    asyncio.run(main())
