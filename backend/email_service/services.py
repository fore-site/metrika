from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from common.metrics import email_sent_total
from urllib.parse import urljoin, urlencode
from .exceptions import EmailPermanentError, EmailTransientError
from .retry import retry_on_transient
import logging
import smtplib
import socket

logger = logging.getLogger(__name__)


class EmailService:

    @retry_on_transient(max_retries=3, base_delay=1, backoff_factor=2)
    def send_verification_email(
        self,
        email: str,
        user_idb64: str,
        token: str,
        name: str = ''
    ) -> None:
        verification_url = self._build_url(
            path='/verify-email',
            user_id=user_idb64,
            token=token,
        )
        context = {
            'verification_url': verification_url,
            'name': name,
        }
        html_body = render_to_string('email/verification.html', context)
        text_body = f'Hi {name},\n\nPlease verify your email by clicking this link: {verification_url}'
        self._send_mail(
            subject='Verify your email address',
            text_body=text_body,
            html_body=html_body,
            to_email=email,
        )

    @retry_on_transient(max_retries=3, base_delay=1, backoff_factor=2)
    def send_password_reset_email(
        self,
        email: str,
        uidb64: str,
        token: str,
        name: str = ''
    ) -> None:
        reset_url = self._build_url(
            path='/reset-password/confirm',
            uid=uidb64,
            token=token,
        )
        context = {
            'reset_url': reset_url,
            'name': name,
        }
        html_body = render_to_string('email/password_reset.html', context)
        text_body = f'Hi {name},\n\nReset your password by clicking this link: {reset_url}'
        self._send_mail(
            subject='Password reset request',
            text_body=text_body,
            html_body=html_body,
            to_email=email,
        )

    # Private helpers
    @staticmethod
    def _send_mail(subject, text_body, html_body, to_email):
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

    @staticmethod
    def _build_url(path: str, **params: str) -> str:
        base = settings.FRONTEND_BASE_URL
        url = urljoin(base, path)
        if params:
            url += '?' + urlencode(params)
        return url