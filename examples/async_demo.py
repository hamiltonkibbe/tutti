#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>
#
import asyncio

from colorama import Fore, Style

from tutti.backends.redis import AsyncLock, AsyncSemaphore


def pprint(data, process_id):
    color = [Fore.CYAN, Fore.MAGENTA, Fore.YELLOW, Fore.GREEN, Fore.BLUE, Fore.RED][process_id]
    print(f"{color}    {data}{Style.RESET_ALL}")


async def use_protected_resource():
    # Just pretend...
    await asyncio.sleep(0.3)


async def access_exclusive_resource(process_id: int) -> None:
    """Use a distributed lock to limit access to a critical resource"""

    async with AsyncLock("demo-time", timeout=5):
        pprint(f"Process {process_id} Entering critical section", process_id)
        await use_protected_resource()
        pprint(f"Process {process_id} Leaving critical section", process_id)


async def access_limited_resource(process_id: int) -> None:
    """Use a distributed semaphore to limit access to a critical resource"""

    async with AsyncSemaphore(lock_name="demo-time", value=2, timeout=5):
        pprint(f"Process {process_id} Entering critical section", process_id)
        await use_protected_resource()
        pprint(f"Process {process_id} Leaving critical section", process_id)


async def main():
    print("\n============================================================================")
    print("Lock demo: Only one process may be in the critical section at a time")
    print("============================================================================")
    lock_tasks = [
        asyncio.create_task(access_exclusive_resource(i)) for i in range(4)
    ]
    await asyncio.gather(*lock_tasks)

    print("\n============================================================================")
    print("Semaphore demo: Up to two processes may be in the critical section at a time")
    print("============================================================================")
    semaphore_tasks = [
        asyncio.create_task(access_limited_resource(i)) for i in range(4)
    ]
    await asyncio.gather(*semaphore_tasks)


if __name__ == "__main__":
    asyncio.run(main())
