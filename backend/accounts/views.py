from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView as BaseLoginView,
    TokenRefreshView as BaseRefreshView,
    TokenVerifyView as BaseVerifyView,
    )
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from common.response import api_response
from email_service.services import EmailService
from .services import AccountService
from .serializers import (
    RegisterSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    VerifyEmailSerializer,
    UserSerializer,
    DeleteAccountSerializer,
    PasswordChangeSerializer,
    ResendVerificationSerializer,
)

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        name = serializer.validated_data['name']

        try:
            user = AccountService().create_user(email, name, password)
        except ValueError as e:
            return api_response(
                status.HTTP_400_BAD_REQUEST,
                message=str(e),
            )

        # Send verification email
        result = AccountService().initiate_email_verification(email)
        if result:
            user_idb64, token = result
            EmailService().send_verification_email(email, user_idb64, token)

        return api_response(
            status.HTTP_201_CREATED,
            message='Registration successful. Kindly check your email to verify your account.',
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_idb64 = serializer.validated_data['user_id']
        token = serializer.validated_data['token']

        success = AccountService().verify_email(user_idb64, token)
        if success:
            return api_response(
                status.HTTP_200_OK,
                message='Email verified successfully.',
            )
        return api_response(
            status.HTTP_400_BAD_REQUEST,
            message='Invalid or expired verification link.',
        )


class LoginView(BaseLoginView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return api_response(
                status.HTTP_200_OK,
                data=response.data,
                message='Login successful.',
            )
        return response


class TokenRefreshView(BaseRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return api_response(
                status.HTTP_200_OK,
                data=response.data,
                message='Token refreshed successfully.',
            )
        return response


class TokenVerifyView(BaseVerifyView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return api_response(
                status.HTTP_200_OK,
                message='Token is valid.',
            )
        return response


class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        result = AccountService().initiate_password_reset(email)
        if result:
            user_idb64, token = result
            EmailService().send_password_reset_email(email, user_idb64, token)

        return api_response(
            status.HTTP_200_OK,
            message='A password reset link has been sent.',
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_idb64 = serializer.validated_data['user_id']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        success = AccountService().confirm_password_reset(user_idb64, token, new_password)
        if success:
            return api_response(
                status.HTTP_200_OK,
                message='Password has been reset successfully.',
            )
        return api_response(
            status.HTTP_400_BAD_REQUEST,
            message='Invalid or expired reset token.',
        )


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return api_response(
            status.HTTP_200_OK,
            data=serializer.data,
        )


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        success = AccountService().change_password(
            user,
            serializer.validated_data['current_password'],
            serializer.validated_data['new_password'],
        )
        if not success:
            return api_response(
                status.HTTP_400_BAD_REQUEST,
                message='Current password is incorrect.',
            )
        return api_response(status.HTTP_200_OK, message='Password changed successfully.')


class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        result = AccountService().resend_verification(email)
        if result:
            user_idb64, token = result
            EmailService().send_verification_email(email, user_idb64, token)

        return api_response(
            status.HTTP_200_OK,
            message='A new verification link has been sent.',
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return api_response(
                status.HTTP_400_BAD_REQUEST,
                message='Refresh token is required.',
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return api_response(
                status.HTTP_400_BAD_REQUEST,
                message='Invalid or expired refresh token.',
            )
        return api_response(status.HTTP_200_OK, message='Logged out successfully.')


class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        success = AccountService().delete_account(user, serializer.validated_data['password'])
        if not success:
            return api_response(
                status.HTTP_400_BAD_REQUEST,
                message='Password is incorrect.',
            )
        return api_response(status.HTTP_200_OK, message='Account deleted successfully.')