#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be

import os
backend = os.getenv("TUTTI_BACKEND", "redis")
if backend == "redis":
    from .backends.redis_backend import Lock, Semaphore, BoundedSemaphore
else:
    raise RuntimeError("Unrecognized backend: {backend}")





__version__ = '0.1.1'
__all__ = ["Lock", "Semaphore", "BoundedSemaphore"]


