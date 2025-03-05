.. Tutti documentation master file, created by
   sphinx-quickstart on Wed Oct 20 20:31:53 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _Github: https://github.com/hamiltonkibbe/tutti

.. image:: tutti.png
      :alt: Tutti logo

Distributed Synchronization for Python
""""""""""""""""""""""""""""""""""""""

Introduction
============
Tutti provides synchronization primitives that let you keep distributed systems synchronized. The API mirrors that of the
synchronization primitives in the builtin :py:mod:`threading` module. It currently ships with a `Redis <https://redis.io/>`_  backend,
but more providers are in the works.

Installing Tutti
================
You can install the latest version of tutti using `pip`

.. code-block:: bash

   $ pip install tutti

Redis Configuration
-------------------
You'll need to have a redis instance somewhere, by default it looks for an instance running on the local machine, but the
connection can be configured using environment variables: ``TUTTI_REDIS_HOST``, ``TUTTI_REDIS_PORT``, ``TUTTI_REDIS_DB``

Getting Started
===============

.. code-block:: python

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
       max_concurrency=5,
       lock=REDIS_LOCK_CONFIG,
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

Roadmap
=======
- AWS/Azure service backends


Author/License
==============

``tutti`` package is written by Hamilton Kibbe and released under the MIT license.

Source code is available on GitHub_. Feel free to contribute!

Table of Contents
=================
.. toctree::
   :maxdepth: 2

   api.rst
