class EmailDeliveryError(Exception):
    """Base exception for email failures."""

class EmailTransientError(EmailDeliveryError):
    """Retryable error (network issues, SMTP server temporarily unavailable)."""

class EmailPermanentError(EmailDeliveryError):
    """Non‑retryable error (invalid recipient, authentication failure)."""