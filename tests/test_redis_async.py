from unittest.mock import AsyncMock

import pytest

from redis.asyncio import Redis
from redis.asyncio.lock import Lock as RedisLock

from tutti.backends.redis.asyncio import Lock, Semaphore, RedisWrapper
from tutti.backends.redis.types import RedisSemaphoreHandle


# region mocks

class MockRedisLock(RedisLock):
    def __init__(self, *args, **kwargs):
        pass


class MockRedisConnection(Redis):
    def __init__(self, *args, **kwargs):
        pass


# endregion

async def test_lock_success():
    """
    Given:
        - A RedisWraper mock that executes correctly
        - A Tutti redis Lock

    When:
        - The lock is acquired
        - The lock is released

    Then:
        - The lock is acquired and released successfully
    """
    # Given
    mock_redis_lock = MockRedisLock()
    mock_redis_wrapper = AsyncMock(spec=RedisWrapper)
    mock_redis_wrapper.acquire_lock.return_value = (mock_redis_lock, True)
    mock_redis_wrapper.release_lock.return_value = True

    # When
    async with Lock(
        connection_url="shouldn't_matter",
        lock_name="test_lock",
        timeout=10,
        conn=MockRedisConnection(),
        redis_wrapper=mock_redis_wrapper
    ) as lock:
        # Then
        assert lock._handle == mock_redis_lock  # type: ignore

    mock_redis_wrapper.acquire_lock.assert_awaited_once()
    mock_redis_wrapper.release_lock.assert_awaited_once()


async def test_lock_failure_to_acquire():
    """
    Given:
        - A RedisWraper mock that does not azquire the lock
        - A Tutti redis Lock

    When:
        - The lock is acquired
        - The lock is released

    Then:
        - A RuntimeError error is raised
        - acquire_lock is awaited
        - release_lock is not awaited
    """
    # Given
    mock_redis_lock = MockRedisLock()
    mock_redis_wrapper = AsyncMock(spec=RedisWrapper)
    mock_redis_wrapper.acquire_lock.return_value = (mock_redis_lock, False)

    # When
    with pytest.raises(RuntimeError):
        async with Lock(
            connection_url="shouldn't_matter",
            lock_name="test_lock",
            timeout=10,
            conn=MockRedisConnection(),
            redis_wrapper=mock_redis_wrapper  # type: ignore
        ) as lock:
            # Then
            assert lock._handle is None

    mock_redis_wrapper.acquire_lock.assert_awaited_once()
    mock_redis_wrapper.release_lock.assert_not_awaited()


async def test_lock_raises():
    """
    Given:
        - A RedisWraper mock that raises when acquiring the lock
        - A Tutti redis Lock

    When:
        - The lock is acquired
        - The lock is released

    Then:
        - A RuntimeError error is raised
        - acquire_lock is awaited
        - release_lock is not awaited
    """
    # Given
    mock_redis_wrapper = AsyncMock(spec=RedisWrapper)
    mock_redis_wrapper.acquire_lock.side_effect = ValueError("something happened")

    # When
    with pytest.raises(RuntimeError):
        async with Lock(
            connection_url="shouldn't_matter",
            lock_name="test_lock",
            timeout=10,
            conn=MockRedisConnection(),
            redis_wrapper=mock_redis_wrapper  # type: ignore
        ) as lock:
            # Then
            assert lock._handle is None

    mock_redis_wrapper.acquire_lock.assert_awaited_once()
    mock_redis_wrapper.release_lock.assert_not_awaited()


async def test_semaphore_success():
    """
    Given:
        - A RedisWraper mock that executes correctly
        - A Tutti redis Semaphore

    When:
        - The semaphore is acquired
        - The semaphore is released

    Then:
        - The semaphore is acquired and released successfully
    """
    # Given
    semaphore_handle = RedisSemaphoreHandle("test_lock", "whatever")
    mock_redis_lock = MockRedisLock()
    mock_redis_wrapper = AsyncMock(spec=RedisWrapper)
    mock_redis_wrapper.acquire_lock.return_value = (mock_redis_lock, True)
    mock_redis_wrapper.release_lock.return_value = True
    mock_redis_wrapper.acquire_semaphore.return_value = semaphore_handle
    mock_redis_wrapper.release_semaphore.return_value = True

    # When
    async with Semaphore(
        connection_url="shouldn't_matter",
        lock_name="test_lock",
        value=1,
        timeout=10,
        conn=MockRedisConnection(),
        redis_wrapper=mock_redis_wrapper  # type: ignore
    ) as semaphore:
        # Then
        assert semaphore._handle == semaphore_handle

    mock_redis_wrapper.acquire_semaphore.assert_awaited_once()
    mock_redis_wrapper.release_semaphore.assert_awaited_once()


async def test_semaphore_fail_to_acquire():
    """
    Given:
        - A RedisWraper mock that fails to acquire the semaphore
        - A Tutti redis Semaphore

    When:
        - The semaphore is acquired
        - The semaphore is released

    Then:
        - A RuntimeError error is raised
        - acquire_semaphore is awaited
        - release_semaphore is not awaited
    """
    # Given
    mock_redis_lock = MockRedisLock()
    mock_redis_wrapper = AsyncMock(spec=RedisWrapper)
    mock_redis_wrapper.acquire_lock.return_value = (mock_redis_lock, True)
    mock_redis_wrapper.release_lock.return_value = True
    mock_redis_wrapper.acquire_semaphore.return_value = None

    # When
    with pytest.raises(RuntimeError):
        async with Semaphore(
            connection_url="shouldn't_matter",
            lock_name="test_lock",
            value=1,
            timeout=10,
            conn=MockRedisConnection(),
            redis_wrapper=mock_redis_wrapper  # type: ignore
        ) as semaphore:
            # Then
            assert semaphore._handle is None

    mock_redis_wrapper.acquire_semaphore.assert_awaited_once()
    await mock_redis_wrapper.release_semaphore.not_awaited()


async def test_semaphore_fail_to_acquire_lock():
    """
    Given:
        - A RedisWraper mock that raises when acquiring the lock
        - A Tutti redis Semaphore

    When:
        - The semaphore is acquired
        - The semaphore is released

    Then:
        - A RuntimeError error is raised
        - acquire_semaphore is not awaited
        - release_semaphore is not awaited
    """
    # Given
    mock_redis_wrapper = AsyncMock(spec=RedisWrapper)
    mock_redis_wrapper.acquire_lock.side_effect = ValueError("something happened")

    # When
    with pytest.raises(RuntimeError):
        async with Semaphore(
            connection_url="shouldn't_matter",
            lock_name="test_lock",
            value=1,
            timeout=10,
            conn=MockRedisConnection(),
            redis_wrapper=mock_redis_wrapper  # type: ignore
        ) as semaphore:
            # Then
            assert semaphore._handle is None

    await mock_redis_wrapper.acquire_semaphore.not_awaited()
    await mock_redis_wrapper.release_semaphore.not_awaited()
