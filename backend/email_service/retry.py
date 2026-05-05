import time
import logging

from .exceptions import EmailTransientError

logger = logging.getLogger(__name__)

def retry_on_transient(max_retries=3, base_delay=1, backoff_factor=2):
    """
    Decorator that retries a function on EmailTransientError,
    with exponential backoff.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = 1  # seconds
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except EmailTransientError as e:
                    last_exception = e
                    if attempt < max_retries:
                        sleep_seconds = base_delay * (backoff_factor ** attempt)
                        logger.warning(
                            f'Retry {attempt+1}/{max_retries} for {func.__name__} '
                            f'due to: {e}. Waiting {delay}s.'
                        )
                        time.sleep(sleep_seconds)
                    else:
                        logger.error(f'All retries exhausted for {func.__name__}')
            raise last_exception
        return wrapper
    return decorator