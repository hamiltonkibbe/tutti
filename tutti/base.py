#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

"""Base classes for distributed synchronization primitives

"""
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional, Type


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