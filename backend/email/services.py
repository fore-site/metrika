from django.conf import settings
from django.core.mail import send_mail


class EmailService:
    """Public interface for all outbound email communication."""

    def send_verification_email(self, email: str, user_idb64: str, token: str) -> None:
        verification_url = self._build_url(
            path='/verify-email',
            user_id=user_idb64,
            token=token,
        )
        send_mail(
            subject='Verify your email address',
            message=f'Click the link to verify your account: {verification_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

    def send_password_reset_email(self, email: str, user_idb64: str, token: str) -> None:
        reset_url = self._build_url(
            path='/reset-password/confirm',
            user_id=user_idb64,
            token=token,
        )
        send_mail(
            subject='Password reset request',
            message=f'Click the link to reset your password: {reset_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

    @staticmethod
    def _build_url(path: str, **params: str) -> str:
        from urllib.parse import urlencode, urljoin
        base = settings.FRONTEND_BASE_URL
        url = urljoin(base, path)
        if params:
            url += '?' + urlencode(params)
        return url