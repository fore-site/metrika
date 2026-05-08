from .exceptions import EmailPermanentError

def email_exception_handler(job, exc_type, exc_value, traceback):
    """Custom handler: return False to stop processing EmailPermanentError."""
    if exc_type is EmailPermanentError:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Permanent email failure, not retrying: {exc_value}')
        return False
    # For all other exceptions (including EmailTransientError), let RQ retry
    return True