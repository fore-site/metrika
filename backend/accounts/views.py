from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from email.services import EmailService

from .services import AccountService
from .serializers import (
    RegisterSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    VerifyEmailSerializer,
    UserSerializer,
)

class RegisterView(generics.CreateAPIView):
    """
    Register a new user. Sends a verification email.
    The account remains inactive until the email is verified.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = AccountService().create_user(email, password)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Generate verification link and send it
        result = AccountService().initiate_email_verification(email)
        if result:
            uidb64, token = result
            EmailService().send_verification_email(email, uidb64, token)

        return Response(
            {'detail': 'Registration successful. Check your email to verify your account.'},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    """Activate a user account via an emailed verification link."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uidb64 = serializer.validated_data['uid']
        token = serializer.validated_data['token']

        success = AccountService().verify_email(uidb64, token)
        if success:
            return Response({'detail': 'Email verified successfully.'})
        return Response(
            {'detail': 'Invalid or expired verification link.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PasswordResetView(APIView):
    """Initiate password reset. Always returns a generic success message."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        result = AccountService().initiate_password_reset(email)
        if result:
            uidb64, token = result
            EmailService().send_password_reset_email(email, uidb64, token)

        # Always return the same message to prevent email enumeration
        return Response(
            {'detail': 'If that email is registered, a password reset link has been sent.'}
        )


class PasswordResetConfirmView(APIView):
    """Confirm password reset using the token sent via email."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uidb64 = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        success = AccountService().confirm_password_reset(uidb64, token, new_password)
        if success:
            return Response({'detail': 'Password has been reset successfully.'})
        return Response(
            {'detail': 'Invalid or expired reset token.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


class MeView(APIView):
    """Return the current authenticated user's profile."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(UserSerializer(user).data)