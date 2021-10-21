![Tutti Logo](docs/tutti.png)

# Distributed Synchronization for Python
Tutti is a nearly drop-in replacement for python's built-in synchronization primitives that lets you fearlessly scale 
your code across processes, machines, clouds and planets.

## Features
 
- Mostly compatible with `threading` primitives
- `asyncio` primitives are on the roadmap
- Redis backend (Azure and AWS backends on the roadmap)

## Installation
The easiest way to install is to just use `pip`:

    pip install tutti

## Example 

```python
from tutti import Lock, Semaphore


with Lock():
   print("Synchronized across machines!")
   access_critical_resource()

with Semaphore(value=2):
   print("Semaphores too!")
   access_less_critical_resource()
```



## License
`tutti` is offered under the MIT license.