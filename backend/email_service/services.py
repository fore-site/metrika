from django.conf import settings
from django.template.loader import render_to_string
from urllib.parse import urljoin, urlencode
from rq import Retry
from .exceptions import EmailTransientError
from .tasks import send_email_task
from accounts.models import LoginAttempt
from django.utils import timezone
import django_rq


class EmailService:

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
        self._enqueue(
            subject='Verify your email address',
            text_body=text_body,
            html_body=html_body,
            to_email=email,
        )

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
        self._enqueue(
            subject='Password reset request',
            text_body=text_body,
            html_body=html_body,
            to_email=email,
        )

    def send_email_change_verification(self, new_email: str, uidb64: str, token: str, name: str = ''):
        verification_url = self._build_url('/email-change/confirm', uid=uidb64, token=token)
        context = {'verification_url': verification_url, 'name': name}
        html_body = render_to_string('email/email_change_verify.html', context)
        text_body = f'Hi {name},\n\nPlease confirm your new email: {verification_url}'
        self._enqueue('Confirm your new email address', text_body, html_body, new_email)

    def send_email_change_notification(self, old_email: str, new_email: str, name: str = ''):
        context = {'name': name, 'old_email': old_email, 'new_email': new_email}
        html_body = render_to_string('email/email_change_notify.html', context)
        text_body = f'Hi {name},\n\nYour email was changed from {old_email} to {new_email}.'
        self._enqueue('Your email address has been changed', text_body, html_body, old_email)

    def send_suspicious_login_notification(self, user, ip_address: str, user_agent: str):
        attempt = LoginAttempt.objects.filter(
            user=user, was_successful=True
        ).order_by('-timestamp').first()
        timestamp = attempt.timestamp if attempt else timezone.now()
        context = {
            'name': user.name,
            'timestamp': timestamp,
            'ip_address': ip_address,
            'user_agent': user_agent,
        }
        html_body = render_to_string('email/suspicious_login.html', context)
        text_body = f'New sign-in to your Metrika account from {ip_address} at {timestamp}.'
        self._enqueue(
            subject='New sign-in to your Metrika account',
            text_body=text_body,
            html_body=html_body,
            to_email=user.email,
        )


    @staticmethod
    def _enqueue(subject, text_body, html_body, to_email):
        django_rq.enqueue(
            send_email_task,
            to_email=[to_email],
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            retry=Retry(
                max=3,
                interval=[1, 2, 4],
            )
        )
        
    @staticmethod
    def _build_url(path: str, **params: str) -> str:
        base = settings.FRONTEND_BASE_URL
        url = urljoin(base, path)
        if params:
            url += '?' + urlencode(params)
        return url