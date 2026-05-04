from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

User = get_user_model()


class AccountService:
    """Public service for all user operations."""

    def create_user(self, email: str, password: str) -> User:
        """
        Register a new user.
        Raises ValueError if the email is already taken.
        """
        if User.objects.filter(email=email).exists():
            raise ValueError("A user with that email already exists.")

        return User.objects.create_user(email=email, password=password)

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
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        return uidb64, token

    def confirm_password_reset(
        self, uidb64: str, token: str, new_password: str
    ) -> bool:
        """
        Validate the reset token and set the new password.
        Returns True on success, False otherwise.
        """
        # Decode the uid
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError):
            return False

        token_generator = PasswordResetTokenGenerator()
        if token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return True
        return False