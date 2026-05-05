from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth import get_user_model
import re

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=150)


    def validate_name(self, value):
        # Strip leading/trailing whitespace and collapse internal spaces
        cleaned = ' '.join(value.split())
        if not cleaned:
            raise serializers.ValidationError("Name cannot be blank.")
        # Length check (min 2)
        if len(cleaned) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        # Character validation: allow letters (any language), digits, spaces, hyphens, apostrophes, periods, commas
        if not re.match(r'^[\w\s\-.,\']+$', cleaned, re.UNICODE):
            raise serializers.ValidationError("Name contains invalid characters.")
        # Disallow leading/trailing punctuation
        if re.match(r'^[-.,\']', cleaned) or re.search(r'[-.,\']$', cleaned):
            raise serializers.ValidationError("Name cannot start or end with punctuation.")
        # Disallow leading or trailing digits
        if not cleaned[0].isalpha() or not cleaned[-1].isalpha():
            raise serializers.ValidationError("Name must start and end with a letter.")
        
        return cleaned

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


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)