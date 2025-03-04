from unittest.mock import Mock

from redis import Redis
from redis.lock import Lock as RedisLock
import pytest

from tutti.backends.redis.sync import Lock, Semaphore, RedisWrapper
from tutti.backends.redis.types import RedisSemaphoreHandle


# region mocks

class MockRedisLock(RedisLock):
    def __init__(self, *args, **kwargs):
        pass


class MockRedisConnection(Redis):
    def __init__(self, *args, **kwargs):
        pass


# endregion

def test_lock_success():
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
    mock_redis_wrapper = Mock(spec=RedisWrapper)
    mock_redis_wrapper.acquire_lock.return_value = (mock_redis_lock, True)
    mock_redis_wrapper.release_lock.return_value = True

    # When
    with Lock(
        connection_url="shouldn't_matter",
        lock_name="test_lock",
        timeout=10,
        conn=MockRedisConnection(),
        redis_wrapper=mock_redis_wrapper  # type: ignore
    ) as lock:
        # Then
        assert lock._handle == mock_redis_lock

    mock_redis_wrapper.acquire_lock.assert_called_once()
    mock_redis_wrapper.release_lock.assert_called_once()


def test_lock_failure_to_acquire():
    """
    Given:
        - A RedisWraper mock that does not azquire the lock
        - A Tutti redis Lock

    When:
        - The lock is acquired
        - The lock is released

    Then:
        - A RuntimeError error is raised
        - acquire_lock is called
        - release_lock is not called
    """
    # Given
    mock_redis_lock = MockRedisLock()
    mock_redis_wrapper = Mock(spec=RedisWrapper)
    mock_redis_wrapper.acquire_lock.return_value = (mock_redis_lock, False)

    # When
    with pytest.raises(RuntimeError):
        with Lock(
            connection_url="shouldn't_matter",
            lock_name="test_lock",
            timeout=10,
            conn=MockRedisConnection(),
            redis_wrapper=mock_redis_wrapper  # type: ignore
        ) as lock:
            # Then
            assert lock._handle is None

    mock_redis_wrapper.acquire_lock.assert_called_once()
    mock_redis_wrapper.release_lock.assert_not_called()


def test_lock_raises():
    """
    Given:
        - A RedisWraper mock that raises when acquiring the lock
        - A Tutti redis Lock
    
    When:
        - The lock is acquired
        - The lock is released
    
    Then:
        - A RuntimeError error is raised
        - acquire_lock is called
        - release_lock is not called
    """
    # Given
    mock_redis_wrapper = Mock(spec=RedisWrapper)
    mock_redis_wrapper.acquire_lock.side_effect = ValueError("something happened")

    # When
    with pytest.raises(RuntimeError):
        with Lock(
            connection_url="shouldn't_matter",
            lock_name="test_lock",
            timeout=10,
            conn=MockRedisConnection(),
            redis_wrapper=mock_redis_wrapper  # type: ignore
        ) as lock:
            # Then
            assert lock._handle is None

    mock_redis_wrapper.acquire_lock.assert_called_once()
    mock_redis_wrapper.release_lock.assert_not_called()


def test_semaphore_success():
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
    mock_redis_wrapper = Mock(spec=RedisWrapper)
    mock_redis_wrapper.acquire_lock.return_value = (mock_redis_lock, True)
    mock_redis_wrapper.release_lock.return_value = True
    mock_redis_wrapper.acquire_semaphore.return_value = semaphore_handle
    mock_redis_wrapper.release_semaphore.return_value = True

    # When
    with Semaphore(
        connection_url="shouldn't_matter",
        lock_name="test_lock",
        value=1,
        timeout=10,
        conn=MockRedisConnection(),
        redis_wrapper=mock_redis_wrapper  # type: ignore
    ) as semaphore:
        # Then
        assert semaphore._handle == semaphore_handle

    mock_redis_wrapper.acquire_semaphore.assert_called_once()
    mock_redis_wrapper.release_semaphore.assert_called_once()


def test_semaphore_fail_to_acquire():
    """
    Given:
        - A RedisWraper mock that fails to acquire the semaphore
        - A Tutti redis Semaphore

    When:
        - The semaphore is acquired
        - The semaphore is released

    Then:
        - A RuntimeError error is raised
        - acquire_semaphore is called
        - release_semaphore is not called
    """
    # Given
    mock_redis_lock = MockRedisLock()
    mock_redis_wrapper = Mock(spec=RedisWrapper)
    mock_redis_wrapper.acquire_lock.return_value = (mock_redis_lock, True)
    mock_redis_wrapper.release_lock.return_value = True
    mock_redis_wrapper.acquire_semaphore.return_value = None

    # When
    with pytest.raises(RuntimeError):
        with Semaphore(
            connection_url="shouldn't_matter",
            lock_name="test_lock",
            value=1,
            timeout=10,
            conn=MockRedisConnection(),
            redis_wrapper=mock_redis_wrapper  # type: ignore
        ) as semaphore:
            # Then
            assert semaphore._handle is None

    mock_redis_wrapper.acquire_semaphore.assert_called_once()
    mock_redis_wrapper.release_semaphore.not_called()


def test_semaphore_fail_to_acquire_lock():
    """
    Given:
        - A RedisWraper mock that raises when acquiring the lock
        - A Tutti redis Semaphore

    When:
        - The semaphore is acquired
        - The semaphore is released

    Then:
        - A RuntimeError error is raised
        - acquire_semaphore is not called
        - release_semaphore is not called
    """
    # Given
    mock_redis_wrapper = Mock(spec=RedisWrapper)
    mock_redis_wrapper.acquire_lock.side_effect = ValueError("something happened")

    # When
    with pytest.raises(RuntimeError):
        with Semaphore(
            connection_url="shouldn't_matter",
            lock_name="test_lock",
            value=1,
            timeout=10,
            conn=MockRedisConnection(),
            redis_wrapper=mock_redis_wrapper  # type: ignore
        ) as semaphore:
            # Then
            assert semaphore._handle is None

    mock_redis_wrapper.acquire_semaphore.not_called()
    mock_redis_wrapper.release_semaphore.not_called()
