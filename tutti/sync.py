from .base import LockABC, SemaphoreABC, LockConfig, SemaphoreConfig

from .backends.redis import (
    Lock as RedisLock,
    Semaphore as RedisSemaphore,
    BoundedSemaphore as RedisBoundedSemaphore,
    RedisLockConfig,
    RedisSemaphoreConfig,
)


class Lock:
    def __new__(cls, config: LockConfig) -> LockABC:
        return _lock_factory(config)


class Semaphore:
    def __new__(cls, config: SemaphoreConfig) -> SemaphoreABC:
        return _semaphore_factory(config)


class BoundedSemaphore:
    def __new__(cls, config: SemaphoreConfig) -> SemaphoreABC:
        return _bounded_semaphore_factory(config)


def _lock_factory(config: LockConfig) -> LockABC:
    """Factory function to create an Lock instance based on the configuration.
    Args:
        config (LockConfig): The tutti lock configuration object.
    Raises:
        NotImplementedError: If the backend is not implemented.
    Returns:
        LockABC: An instance of the appropriate Lock backend.
    """
    match config:
        case RedisLockConfig():
            return RedisLock(
                connection_url=config.connection_url,
                lock_name=config.name,
                timeout=config.timeout,
                blocking=config.blocking,
            )
        case _:
            raise NotImplementedError(f"The {config} backend is not implemented for sync locks.")


def _semaphore_factory(config: SemaphoreConfig) -> SemaphoreABC:
    """Factory function to create an Semaphore instance based on the configuration.
    Args:
        config (SemaphoreConfig): The tutti semaphore configuration object.
    Raises:
        NotImplementedError: If the backend is not implemented.
    Returns:
        SemaphoreABC: An instance of the appropriate Semaphore backend.
    """
    match config:
        case RedisSemaphoreConfig():
            return RedisSemaphore(
                connection_url=config.connection_url,
                value=config.max_concurrency,
                lock_name=config.lock.name,
                timeout=config.lock.timeout,
            )
        case _:
            raise NotImplementedError(f"The {config} backend is not implemented for sync semaphores.")


def _bounded_semaphore_factory(config: SemaphoreConfig) -> SemaphoreABC:
    """Factory function to create an BoundedSemaphore instance based on the configuration.
    Args:
        config (SemaphoreConfig): The tutti semaphore configuration object.
    Raises:
        NotImplementedError: If the backend is not implemented.
    Returns:
        SemaphoreABC: An instance of the appropriate BoundedSemaphore backend.
    """
    match config:
        case RedisSemaphoreConfig():
            return RedisBoundedSemaphore(
                connection_url=config.connection_url,
                value=config.max_concurrency,
                lock_name=config.lock.name,
                timeout=config.lock.timeout,
            )
        case _:
            raise NotImplementedError(f"The {config} backend is not implemented for sync bounded semaphores.")


__all__ = ["Lock", "Semaphore", "BoundedSemaphore"]
