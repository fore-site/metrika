from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()


class AccountService:
    """Public service for all user operations."""

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
        Returns True on success, False otherwise.
        """
        # Decode the user_idb64
        try:
            user_id = force_str(urlsafe_base64_decode(user_idb64))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError):
            return False

        token_generator = PasswordResetTokenGenerator()
        if token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return True
        return False

    def initiate_email_verification(self, email: str) -> tuple[str, str] | None:
        """
        Generate verification uid+token for a user.
        Returns (uidb64, token) if user exists, else None.
        """
        user = self.get_user_by_email(email)
        if user is None:
            return None
        token = default_token_generator.make_token(user)
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
        if default_token_generator.check_token(user, token):
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

    def delete_account(self, user: User, password: str) -> bool:
        """Delete user if password matches. Cascades to sites, events, etc. later."""
        if not user.check_password(password):
            return False
        user.delete()
        return True