import pytest

from tutti.configuration import RedisLockConfig, RedisSemaphoreConfig
from tutti.asyncio import Lock, Semaphore, BoundedSemaphore


from tutti.backends.redis import (
    AsyncLock as RedisLock,
    AsyncSemaphore as RedisSemaphore,
    AsyncBoundedSemaphore as RedisBoundedSemaphore,
)

# region mocks

FAKE_CONNECTION_URL = "redis://notarealplace:6379/0"


# endregion


def test_redis_lock_factory():
    """
    Given:
        - A RedisLockConfig object
    When:
        - The lock factory is called with the config object
    Then:
        - The correct RedisLock instance is created
    """
    # Given
    config = RedisLockConfig(
        connection_url=FAKE_CONNECTION_URL,
        name="test_lock",
        timeout=10,
    )

    # When
    lock = Lock(config)

    # Then
    assert isinstance(lock, RedisLock)


def test_redis_semaphore_factory():
    """
    Given:
        - A RedisSemaphoreConfig object
    When:
        - The semaphore factory is called with the config object
    Then:
        - The correct RedisSemaphore instance is created
    """
    # Given
    config = RedisSemaphoreConfig(
        connection_url=FAKE_CONNECTION_URL,
        max_concurrency=5,
        name="test_semaphore",
        lock_timeout=10,
    )

    # When
    semaphore = Semaphore(config)

    # Then
    assert isinstance(semaphore, RedisSemaphore)


def test_redis_bounded_semaphore_factory():
    """
    Given:
        - A RedisSemaphoreConfig object
    When:
        - The bounded semaphore factory is called with the config object
    Then:
        - The correct RedisBoundedSemaphore instance is created
    """
    # Given
    config = RedisSemaphoreConfig(
        connection_url=FAKE_CONNECTION_URL,
        max_concurrency=5,
        name="test_semaphore",
        lock_timeout=10,
    )

    # When
    bounded_semaphore = BoundedSemaphore(config)

    # Then
    assert isinstance(bounded_semaphore, RedisBoundedSemaphore)


def test_redis_lock_factory_not_implemented():
    """
    Given:
        - A random class
        - An instance of the random class used as the config
    When:
        - The lock factory is called with the config object
    Then:
        - NotImplementedError is raised
    """
    # Given
    class RandomClass:
        pass
    config = RandomClass()

    # When/Then
    with pytest.raises(NotImplementedError):
        Lock(config)  # type: ignore
