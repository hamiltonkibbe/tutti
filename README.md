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
from tutti.backends.redis import Lock, Semaphore
from tutti.backends.redis import AsyncLock, AsyncSemaphore


with Semaphore(lock_name="demo-time", value=2, timeout=5):
    print("Semaphores too!")
    access_less_critical_resource()


async with AsyncLock("demo-time", timeout=5):
    print("Synchronized across machines!")
    await access_critical_resource()
   
async with AsyncSemaphore(lock_name="demo-time", value=2, timeout=5):
    print("Synchronized across machines!")
    await access_critical_resource()

```



## License
`tutti` is offered under the MIT license.