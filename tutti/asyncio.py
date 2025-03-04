from .base import (
    AsyncLockABC,
    AsyncSemaphoreABC,
    LockConfig,
    SemaphoreConfig,
)

from .backends.redis import (
    AsyncLock as RedisAsyncLock,
    AsyncSemaphore as RedisAsyncSemaphore,
    AsyncBoundedSemaphore as RedisAsyncBoundedSemaphore,
    RedisLockConfig,
    RedisSemaphoreConfig,
)


class Lock:
    def __new__(cls, config: LockConfig) -> AsyncLockABC:
        return _lock_factory(config)


class Semaphore:
    def __new__(cls, config: SemaphoreConfig) -> AsyncSemaphoreABC:
        return _semaphore_factory(config)


class BoundedSemaphore:
    def __new__(cls, config: SemaphoreConfig) -> AsyncSemaphoreABC:
        return _bounded_semaphore_factory(config)


def _lock_factory(config: LockConfig) -> AsyncLockABC:
    """Factory function to create an AsyncLock instance based on the configuration.
    Args:
        config (LockConfig): The tutti lock configuration object.
    Raises:
        NotImplementedError: If the backend is not implemented.
    Returns:
        AsyncLockABC: An instance of the appropriate AsyncLock backend.
    """
    match config:
        case RedisLockConfig():
            return RedisAsyncLock(
                connection_url=config.connection_url,
                lock_name=config.name,
                timeout=config.timeout,
                blocking=config.blocking,
            )
        case _:
            raise NotImplementedError(f"The {config} backend is not implemented for asyncio locks.")


def _semaphore_factory(config: SemaphoreConfig) -> AsyncSemaphoreABC:
    """Factory function to create an AsyncSemaphore instance based on the configuration.
    Args:
        config (SemaphoreConfig): The tutti semaphore configuration object.
    Raises:
        NotImplementedError: If the backend is not implemented.
    Returns:
        AsyncSemaphoreABC: An instance of the appropriate AsyncSemaphore backend.
    """
    match config:
        case RedisSemaphoreConfig():
            return RedisAsyncSemaphore(
                connection_url=config.connection_url,
                value=config.max_concurrency,
                lock_name=config.lock.name,
                timeout=config.lock.timeout,
            )
        case _:
            raise NotImplementedError(f"The {config} backend is not implemented for asyncio semaphores.")


def _bounded_semaphore_factory(config: SemaphoreConfig) -> AsyncSemaphoreABC:
    """Factory function to create an AsyncBoundedSemaphore instance based on the configuration.
    Args:
        config (SemaphoreConfig): The tutti semaphore configuration object.
    Raises:
        NotImplementedError: If the backend is not implemented.
    Returns:
        AsyncSemaphoreABC: An instance of the appropriate AsyncBoundedSemaphore backend.
    """
    match config:
        case RedisSemaphoreConfig():
            return RedisAsyncBoundedSemaphore(
                connection_url=config.connection_url,
                value=config.max_concurrency,
                lock_name=config.lock.name,
                timeout=config.lock.timeout,
            )
        case _:
            raise NotImplementedError(f"The {config} backend is not implemented for asyncio bounded semaphores.")


__all__ = ["Lock", "Semaphore", "BoundedSemaphore"]
