#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be

import os
backend = os.getenv("TUTTI_BACKEND", "redis")
if backend == "redis":
    from .backends.redis import Lock
    from .backends.redis import Semaphore
    from .backends.redis import BoundedSemaphore
elif backend == "redis-async":
    from .backends.redis import AsyncLock as Lock
    from .backends.redis import AsyncSemaphore as Semaphore
    from .backends.redis import AsyncBoundedSemaphore as BoundedSemaphore
else:
    raise RuntimeError("Unrecognized backend: {backend}")


__version__ = '1.0.0'
__all__ = ["Lock", "Semaphore", "BoundedSemaphore"]
