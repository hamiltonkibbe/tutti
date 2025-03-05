#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

"""Base classes for distributed synchronization primitives

"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import TracebackType
from typing import Optional, Type


TUTTI_LOGGER_NAME = "tutti"


@dataclass(kw_only=True)
class LockConfig(ABC):
    """Lock congfiguration Base class.

    Parameters:
        name (str):
            The name of the Redis Lock.
        timeout (float):
            The timeout for acquiring the lock, in seconds
        blocking (bool):
            Whether to block while waiting for the lock to be released. Defaults to `True`.
    """
    name: str
    timeout: float
    blocking: bool = True


@dataclass
class SemaphoreConfig(ABC):
    """Semaphore congfiguration Base class.

    Parameters:
        name (str):
            The name of the Semaphore.
        max_concurrency (int):
            The maximum number of concurrent accesses to the resource.
    """
    name: str
    max_concurrency: int


class LockABC(ABC):
    """Abstract base class for Lock primitive

    Mostly compatible with :py:class:`threading.Lock`.
    """

    @abstractmethod
    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """Acquire a lock.

        Parameters
        ----------
        blocking: bool
            Whether or not to block waiting for the lock. If blocking is set to `True`, block for up to `timeout`
            seconds (or forever if `timeout` is `None`).

        timeout: Optional[float]
            Number of seconds to wait for the lock if it is not immediately available. Defaults to `None`.

        Returns
        -------
        success : bool
            `True` if lock was acquired successfully, `False` otherwise.
        """
        pass

    @abstractmethod
    def release(self) -> None:
        """Release a lock.

        Returns
        -------
        None

        Raises
        ------
        `RuntimeError`
            if called on an unlocked Lock.
        """
        pass

    @abstractmethod
    def locked(self) -> bool:
        """Return `True` if the lock is locked

        Returns
        -------
        locked: bool
            `True` if the lock is held by anyone, not just this process.

        """
        pass

    @abstractmethod
    def __enter__(self) -> "LockABC":
        pass

    @abstractmethod
    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]) -> Optional[bool]:
        pass


class SemaphoreABC(ABC):
    """Abstract Base Class for Semaphore primitive

    Mostly compatible with :py:class:`threading.Semaphore`.
    """

    @abstractmethod
    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        pass

    @abstractmethod
    def release(self, n: int = 1) -> None:
        pass

    @abstractmethod
    def __enter__(self) -> "SemaphoreABC":
        pass

    @abstractmethod
    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]) -> Optional[bool]:
        pass


class AsyncLockABC(ABC):
    """Abstract base class for Lock primitive

    Mostly compatible with :py:class:`asyncio.Lock`.
    """

    @abstractmethod
    async def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """Acquire a lock.

        Parameters
        ----------
        blocking: bool
            Whether or not to block waiting for the lock. If blocking is set to `True`, block for up to `timeout`
            seconds (or forever if `timeout` is `None`).

        timeout: Optional[float]
            Number of seconds to wait for the lock if it is not immediately available. Defaults to `None`.

        Returns
        -------
        success : bool
            `True` if lock was acquired successfully, `False` otherwise.
        """
        pass

    @abstractmethod
    async def release(self) -> None:
        """Release a lock.

        Returns
        -------
        None

        Raises
        ------
        `RuntimeError`
            if called on an unlocked Lock.
        """
        pass

    @abstractmethod
    async def locked(self) -> bool:
        """Return `True` if the lock is locked

        Returns
        -------
        locked: bool
            `True` if the lock is held by anyone, not just this process.

        """
        pass

    @abstractmethod
    async def __aenter__(self) -> "AsyncLockABC":
        pass

    @abstractmethod
    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]) -> Optional[bool]:
        pass


class AsyncSemaphoreABC(ABC):
    """Abstract Base Class for Semaphore primitive

    Mostly compatible with :py:class:`asyncio.Semaphore`.
    """

    @abstractmethod
    async def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        pass

    @abstractmethod
    async def release(self) -> None:
        pass

    @abstractmethod
    async def __aenter__(self) -> "AsyncSemaphoreABC":
        pass

    @abstractmethod
    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]) -> Optional[bool]:
        pass
