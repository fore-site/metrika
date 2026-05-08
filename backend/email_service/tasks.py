import smtplib
import socket
import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .exceptions import EmailPermanentError, EmailTransientError
from common.metrics import email_sent_total

logger = logging.getLogger(__name__)

def send_email_task(to_email, subject, text_body, html_body):
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
