from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as TokenObtainSerializer
from .services import AccountService
from common.validators import validate_name_field


User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=150)


    def validate_name(self, value):
        return validate_name_field(value)

    def validate_password(self, value):

        validate_password(value)
        return value


User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainSerializer):
    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            "password": attrs["password"],
        }
        user = authenticate(**authenticate_kwargs)

        if user is not None:
            # user is authenticated and active/unsuspended. parent handles token generation
            return super().validate(attrs)

        # Authentication failed. Check if the password was correct.
        email = attrs.get(self.username_field)
        password = attrs.get("password")
        existing_user = AccountService().get_user_by_email(email)

        if existing_user and existing_user.check_password(password):
            # Password correct – raise a tailored message based on account status
            if not existing_user.is_active:
                raise AuthenticationFailed(
                    detail="Account not yet activated. Please check your email to verify your account.",
                    code="inactive",
                )
            elif existing_user.is_suspended:
                # Still generic for suspended (security)
                raise AuthenticationFailed(
                    detail="Your account has been suspended. Kindly contact support.",
                    code="suspended",
                )
        # Fallback
        raise AuthenticationFailed(
            detail="No active account found for the provided credentials.",
            code="no_active_account",
        )

class TokenObtainPairResponseSerializer(serializers.Serializer): # For documentation purposes only
    access = serializers.CharField(read_only=True)


class TokenObtainPairSerializer(serializers.Serializer): # For documentation purposes only
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True) 

    def validate_password(self, value):
        validate_password(value)
        return value

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'is_staff', 'is_active', 'date_joined']
        read_only_fields = fields


class InitiateEmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyEmailSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    token = serializers.CharField()


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class NameChangeSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)

    def validate_name(self, value):
        return validate_name_field(value)

class InitiateEmailChangeSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class ConfirmEmailChangeSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    token = serializers.CharField()


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)