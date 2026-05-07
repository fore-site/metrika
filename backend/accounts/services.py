from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.conf import settings
from ipware import get_client_ip as _get_client_ip
import logging
from datetime import timedelta
from django.utils import timezone
from .models import LoginAttempt

User = get_user_model()
logger = logging.getLogger(__name__)


class EmailChangeTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "email-change"

class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "email-verification"

email_change_token_generator = EmailChangeTokenGenerator()
email_verification_token_generator = EmailVerificationTokenGenerator()

class AccountService:
    """Public service for all user operations."""

    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15


    def create_user(self, email: str, name: str, password: str) -> User:
        """
        Register a new user.
        Raises ValueError if the email is already taken.
        """
        if User.objects.filter(email=email).exists():
            raise ValueError("A user with that email already exists.")

        return User.objects.create_user(email=email, password=password, name=name)

    def get_user_by_email(self, email: str) -> User | None:
        """Return the user for a given email, or None."""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    def get_user_by_id(self, user_id: int) -> User | None:
        """Return the user for a given id, or None."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def initiate_password_reset(self, email: str) -> tuple[str, str] | None:
        """
        Generate a one-time token and a URL-safe user identifier.
        Returns (uidb64, token) if the email exists, else None.
        """
        user = self.get_user_by_email(email)
        if user is None:
            return None

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        user_idb64 = urlsafe_base64_encode(force_bytes(user.pk))
        return user_idb64, token

    def confirm_password_reset(
        self, user_idb64: str, token: str, new_password: str
    ) -> bool:
        """
        Validate the reset token and set the new password.
        Returns user on success, None otherwise.
        """
        # Decode the user_idb64
        try:
            user_id = force_str(urlsafe_base64_decode(user_idb64))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError):
            return None

        token_generator = PasswordResetTokenGenerator()
        if token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return user
        return None

    def initiate_email_verification(self, email: str) -> tuple[str, str] | None:
        """
        Generate verification uid+token for a user.
        Returns (uidb64, token) if user exists, else None.
        """
        user = self.get_user_by_email(email)
        if user is None:
            return None
        token = email_verification_token_generator.make_token(user)
        user_idb64 = urlsafe_base64_encode(force_bytes(user.pk))
        return user_idb64, token

    def verify_email(self, user_idb64: str, token: str) -> bool:
        """
        Confirm email address.
        Returns True if token is valid and user is activated.
        """
        try:
            user_id = force_str(urlsafe_base64_decode(user_idb64))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError):
            return False
        if user.is_active == True:
            return True
        if email_verification_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return True
        return False


    def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        """Return True if password changed, False if current password is wrong."""
        if not user.check_password(current_password):
            return False
        validate_password(new_password, user=user)
        user.set_password(new_password)
        user.save()
        return True

    def resend_verification(self, email: str) -> tuple[str, str] | None:
        """Generate new verification token if user exists and is inactive."""
        user = self.get_user_by_email(email)
        if user is None or user.is_active:
            return None
        token = default_token_generator.make_token(user)
        user_idb64 = urlsafe_base64_encode(force_bytes(user.pk))
        return user_idb64, token
    

    def update_name(self, user: User, new_name: str) -> User:
        """Update the user's name."""
        user.name = new_name
        user.save()
        return user


    def initiate_email_change(self, user: User, new_email: str, password: str) -> tuple[str, str]:
        """Initiate email change process. 
        Returns (user_idb64, token) for the new email, else raises ValueError for existing emails or invalid password.
        """
        if not user.check_password(password):
            raise ValueError("Current password is incorrect.")
        if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
            raise ValueError("A user with that email already exists.")
        token = email_change_token_generator.make_token(user)
        user_idb64 = urlsafe_base64_encode(force_bytes(user.pk))

        cache_key = f"email_change:{user.pk}"
        cache.set(cache_key, new_email, timeout=settings.EMAIL_CHANGE_TIMEOUT)
        return user_idb64, token


    def confirm_email_change(self, user_idb64: str, token: str):
        """Returns (user, old email) on success or None"""
        try:
            user_id = force_str(urlsafe_base64_decode(user_idb64))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError):
            return None
        
        if not email_change_token_generator.check_token(user, token):
            return None

        cache_key = f"email_change:{user.pk}"
        new_email = cache.get(cache_key)
        if not new_email:
            return None
        

        old_email = user.email
        user.email = new_email
        user.save()
        cache.delete(cache_key)
        return user, old_email

    

    def delete_account(self, user: User, password: str) -> bool:
        """Delete user if password matches. Cascades to sites, events, etc. later."""
        if not user.check_password(password):
            return False
        user.delete()
        return True
    
    
    def record_login_attempt(self, email: str, ip_address: str, user_agent: str,
                             was_successful: bool, user=None):
        """Persist every login attempt for later analysis."""
        LoginAttempt.objects.create(
            user=user,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            was_successful=was_successful,
        )

    def detect_suspicious_login(self, user, ip_address: str) -> bool:
        """
        Return True if this login looks suspicious.
        Criteria:
        - New IP (not used in last 30 days)
        """
        recent_window = timezone.now() - timedelta(days=30)
        previous = LoginAttempt.objects.filter(
            user=user,
            was_successful=True,
            timestamp__gte=recent_window,
        )

        # If no previous successful logins, this is first login
        if not previous.exists():
            return False

        # Check IP
        used_ips = set(previous.values_list('ip_address', flat=True))
        if ip_address not in used_ips:
            logger.info(f'Suspicious login for user {user.id}: new IP {ip_address}')
            return True

        return False

    def get_latest_suspicious_attempt(self, user):
        """For notification details – get the most recent login attempt for this user."""
        return LoginAttempt.objects.filter(
            user=user, was_successful=True
        ).order_by('-timestamp').first()

    def get_client_ip(self, request):
        """Extract real client IP, even behind proxies."""
        ip, _ = _get_client_ip(request)
        if ip is None:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def get_user_agent(self, request):
        """Extract user agent string."""
        return request.META.get('HTTP_USER_AGENT', '')
