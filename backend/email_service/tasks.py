import smtplib
import socket
from django.core.mail import EmailMultiAlternatives
import logging
import requests
from django.conf import settings
from .exceptions import EmailPermanentError, EmailTransientError
from common.metrics import email_sent_total

logger = logging.getLogger(__name__)

def send_email_task(to_email: str, subject: str, text_body: str, html_body: str,
                    email_type: str = 'generic'):
    """
    email_type is one of: verification, password_reset, suspicious_login, etc.
    """
    try:
        response = requests.post(
            url='https://api.brevo.com/v3/smtp/email',
            headers={
                'accept': 'application/json',
                'api-key': settings.BREVO_API_KEY,
                'content-type': 'application/json',
            },
            json={
                'sender': {'email': settings.DEFAULT_FROM_EMAIL},
                'to': [{'email': to_email}],
                'subject': subject,
                'textContent': text_body,
                'htmlContent': html_body,
            },
            timeout=30,
        )
        response.raise_for_status()
        # Success – increment metric
        email_sent_total.labels(type=email_type, status='success').inc()
        return
    except requests.HTTPError as e:
        # HTTP error (4xx or 5xx)
        status_code = e.response.status_code if e.response is not None else 0
        if 400 <= status_code < 500:
            # Permanent – don't retry
            email_sent_total.labels(type=email_type, status='permanent_failure').inc()
            raise EmailPermanentError(f'Brevo API {status_code}: {e}') from e
        else:
            # 5xx or no response – transient, let RQ retry
            email_sent_total.labels(type=email_type, status='transient_failure').inc()
            raise EmailTransientError(f'Brevo API {status_code}: {e}') from e
    except requests.Timeout as e:
        email_sent_total.labels(type=email_type, status='transient_failure').inc()
        raise EmailTransientError(f'Timeout: {e}') from e
    except Exception as e:
        # Unexpected error – treat as transient
        email_sent_total.labels(type=email_type, status='transient_failure').inc()
        raise EmailTransientError(f'Unexpected error: {e}') from e


def send_console_email_task(to_email, subject, text_body, html_body):
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    msg.attach_alternative(html_body, 'text/html')
    try:
        msg.send()
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Invalid recipient email address: {to_email}", exc_info=True)
        email_sent_total.labels(type='verification', status='permanent_failure').inc()
        raise EmailPermanentError("Invalid recipient email address.") from e
    except smtplib.SMTPAuthenticationError as e:
        logger.error("SMTP authentication failed. Check email server credentials.", exc_info=True)
        email_sent_total.labels(type='verification', status='permanent_failure').inc()
        raise EmailPermanentError("Email server authentication failed.") from e
    except (smtplib.SMTPException, socket.error) as e:
            # Transient error e.g network issues, SMTP server temporarily unavailable
        logger.error(f"Transient error occurred while sending email to {to_email}: {e}", exc_info=True)
        email_sent_total.labels(type='verification', status='transient_failure').inc()
        raise EmailTransientError("Failed to send email due to a transient error. Please try again later.") from e
    except Exception as e:
        logger.error(f"Unexpected error occurred while sending email to {to_email}: {e}", exc_info=True)
        email_sent_total.labels(type='verification', status='transient_failure').inc()
        raise EmailTransientError("An unexpected error occurred while sending email.") from e
