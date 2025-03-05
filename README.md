![Tutti Logo](docs/tutti.png)

*adverb* -- with all voices or instruments together.

# Distributed Synchronization for Python
Tutti is a nearly drop-in replacement for python's built-in synchronization primitives that lets you fearlessly scale 
your code across processes, machines, clouds and planets.

Full Documentation available [on Read The Docs](https://tutti-py.readthedocs.io/en/latest/)
## Features
 
- Mostly compatible with `threading` primitives
- Redis backend (Azure and AWS backends on the roadmap)

## Installation
The easiest way to install is to just use `pip`:

    pip install tutti

## Example 

```python
from tutti import Lock
from tutti import Semaphore
from tutti.asyncio import Lock as AsyncLock
from tutti.asyncio import Semaphore as AsyncSemaphore
from tutti.configuration import RedisLockConfig
from tutti.configuration import RedisSemaphoreConfig


REDIS_LOCK_CONFIG = RedisLockConfig(
    connection_url="redis://localhost:6379/0",
    name="test_lock",
    timeout=10,
    blocking=True,
)

REDIS_SEMAPHORE_CONFIG = RedisSemaphoreConfig(
    connection_url="redis://localhost:6379/0",
    name="test_semaphore",
    max_concurrency=5,
    lock_timeout=10
)


with Lock(REDIS_LOCK_CONFIG):
    print("Locks!")
    access_critical_resource()


with Semaphore(REDIS_SEMAPHORE_CONFIG):
    print("Semaphores too!?")
    access_less_critical_resource()


async with AsyncLock(REDIS_LOCK_CONFIG):
    print("Synchronized across machines!")
    await access_critical_resource()


async with AsyncSemaphore(REDIS_SEMAPHORE_CONFIG):
    print("And it supports asyncio!?")
    await access_critical_resource()

```



## License
`tutti` is offered under the MIT license.