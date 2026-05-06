from django.conf import settings
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView as BaseLoginView,
    TokenRefreshView as BaseRefreshView,
    TokenVerifyView as BaseVerifyView,
    )
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from common.response import api_response
from email_service.services import EmailService
from email_service.exceptions import EmailTransientError, EmailPermanentError
from .services import AccountService
from .serializers import (
    NameChangeSerializer,
    InitiateEmailChangeSerializer,
    ConfirmEmailChangeSerializer,
    RegisterSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    TokenObtainPairResponseSerializer,
    VerifyEmailSerializer,
    UserSerializer,
    DeleteAccountSerializer,
    PasswordChangeSerializer,
    ResendVerificationSerializer,
)
import logging 

logger = logging.getLogger(__name__)


from drf_spectacular.utils import extend_schema
from common.openapi import envelope_success, envelope_error

@extend_schema(
    summary='Register a new user',
    description='Creates an inactive user and sends a verification email.',
    request=RegisterSerializer,
    responses={
        201: envelope_success(
            description='Registration successful – check email for verification link.'
        ),
        400: envelope_error(),
    },
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
            try:
                EmailService().send_verification_email(email, user_idb64, token, name=name)
            except EmailTransientError as e:
                logger.error(f"Transient error sending verification email to {email}: {e}", exc_info=True)
                return api_response(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Failed to send verification email. Please request a new one."
                )
            except EmailPermanentError as e:
                logger.error(f"Permanent error sending verification email to {email}: {e}", exc_info=True)
                return api_response(
                    status.HTTP_400_BAD_REQUEST,
                    message="Invalid email address. Please provide a valid email."
                )
        return api_response(
            status.HTTP_201_CREATED,
            message='Registration successful. Kindly check your email to verify your account.',
        )

@extend_schema(
    summary='Verify email after registration',
    description="Sets a registered user's inactive status to active.",
    request=VerifyEmailSerializer,
    responses={
        200: envelope_success(
            description='Email successfully verified.'
        ),
    },
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

@extend_schema(
    summary='Obtain JWT tokens',
    description="Returns an access token in the body and sets an httpOnly refresh token cookie.",
    responses={
        200: envelope_success(
            data_serializer=TokenObtainPairResponseSerializer(),
            description='Login successful.'
        ),
    },
)
class LoginView(BaseLoginView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            refresh_token = response.data['refresh']
            data = {'access': response.data['access']}
            
            samesite = settings.REFRESH_TOKEN_COOKIE_SAMESITE
            max_age = settings.REFRESH_TOKEN_MAX_AGE

            res = api_response(
                status.HTTP_200_OK,
                data=data,
                message='Login successful.',
            )
            res.set_cookie(
                key=settings.REFRESH_TOKEN_COOKIE_NAME,
                value=str(refresh_token),
                httponly=settings.REFRESH_TOKEN_COOKIE_HTTPONLY,
                max_age=max_age,
                samesite=samesite,
                path='/api/auth/token/refresh/',  # Only send cookie to refresh endpoint
            )

            get_token(request)  # Ensure CSRF token is set in the response cookies
            return res
        return response

@extend_schema(
    summary='Obtain new access token',
    description="Returns an access token in the body.",
    responses={
        200: envelope_success(
            data_serializer=TokenObtainPairResponseSerializer(),
            description='Token successfully refreshed.'
        ),
    },
)
@method_decorator(csrf_protect, name='dispatch')
class TokenRefreshView(BaseRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            refresh_token = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
            if not refresh_token:
                refresh_token = request.data.get('refresh')
                if not refresh_token:
                    return api_response(
                        status.HTTP_400_BAD_REQUEST,
                        message='Refresh token is required.',
                    )
                
            try:
                token = RefreshToken(refresh_token)
            except TokenError:
                return api_response(
                    status.HTTP_400_BAD_REQUEST,
                    message='Invalid or expired refresh token.',
                )
            
            try:
                token.blacklist()  # Blacklist the old refresh token
            except Exception as e:
                logger.error(f"Error blacklisting refresh token: {e}", exc_info=True)

            token.set_jti()  # Generate a new jti for the new token
            token.set_exp()
            new_refresh = str(token)
            res = api_response(
                status.HTTP_200_OK,
                data=response.data,
                message='Token refreshed successfully.',
            )
            res.set_cookie(
                key=settings.REFRESH_TOKEN_COOKIE_NAME,
                value=new_refresh,
                httponly=settings.REFRESH_TOKEN_COOKIE_HTTPONLY,
                max_age=settings.REFRESH_TOKEN_MAX_AGE,
                samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
                path='/api/auth/token/refresh/',
            )
        return response


@extend_schema(
    summary='Verify JWT token validity',
    description="Verifies if a JWT token is valid.",
    responses={
        200: envelope_success(
            description='Token is valid.'
        ),
    },
)
class TokenVerifyView(BaseVerifyView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return api_response(
                status.HTTP_200_OK,
                message='Token is valid.',
            )
        return response


@extend_schema(
    summary='Reset password',
    description="Sends a password reset link to user's mail.",
    request=PasswordResetSerializer,
    responses={
        200: envelope_success(
            description='A password reset link has been sent.'
        ),
    },
)
class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        result = AccountService().initiate_password_reset(email)
        if result:
            user = AccountService().get_user_by_email(email)
            name = user.name if user else ''
            user_idb64, token = result
            try:
                EmailService().send_password_reset_email(email, user_idb64, token, name=name)
            except EmailTransientError as e:
                logger.error(f"Transient error sending password reset email to {email}: {e}", exc_info=True)
                return api_response(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Failed to send password reset email. Please request a new one."
                )
            except EmailPermanentError as e:
                logger.error(f"Permanent error sending password reset email to {email}: {e}", exc_info=True)
                return api_response(
                    status.HTTP_400_BAD_REQUEST,
                    message="Invalid email address. Please provide a valid email."
                )
        return api_response(
            status.HTTP_200_OK,
            message='A password reset link has been sent.',
        )

@extend_schema(
    summary='Confirm password reset',
    description="Confirms new password has been set.",
    request=PasswordResetSerializer,
    responses={
        200: envelope_success(
            description='Password has been reset successfully.'
        ),
    },
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

@extend_schema(
    summary='View and update user profile',
    description="Returns user's current or updated detail.",
    request=NameChangeSerializer,
    responses={
        200: envelope_success(
            data_serializer=UserSerializer(),
            description='A password reset link has been sent.'
        ),
    },
)
class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return api_response(
            status.HTTP_200_OK,
            data=serializer.data,
        )

    def patch(self, request):
        serializer = NameChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_name = serializer.validated_data['name']
        AccountService().update_name(request.user, new_name)
        # Return updated user data
        user_serializer = UserSerializer(request.user)
        return api_response(200, data=user_serializer.data, message='Name updated.')


@extend_schema(
    summary='Change user password',
    description="Sets new password for an authenticated user and deletes httponly refresh token cookie.",
    request=PasswordChangeSerializer,
    responses={
        200: envelope_success(
            description='Password changed successfully.'
        ),
    },
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
        # Invalidate all existing tokens for the user after password change
        OutstandingToken.objects.filter(user=user).delete()

        res = api_response(status.HTTP_200_OK, message='Password changed successfully. Kindly login again.')
        res.delete_cookie(settings.REFRESH_TOKEN_COOKIE_NAME, path='/api/auth/token/refresh/')
        return res

@extend_schema(
    summary='Resend email verification link',
    description="Resends a newly generated email verification link to the user's email.",
    request=ResendVerificationSerializer,
    responses={
        200: envelope_success(
            description='A new verification link has been sent.'
        ),
    },
)
class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        result = AccountService().resend_verification(email)
        if result:
            user = AccountService().get_user_by_email(email)
            name = user.name if user else ''
            user_idb64, token = result
            try:
                EmailService().send_verification_email(email, user_idb64, token, name=name)
            except EmailTransientError as e:
                logger.error(f"Transient error sending verification email to {email}: {e}", exc_info=True)
                return api_response(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Failed to send verification email. Please request a new one."
                )
            except EmailPermanentError as e:
                logger.error(f"Permanent error sending verification email to {email}: {e}", exc_info=True)
                return api_response(
                    status.HTTP_400_BAD_REQUEST,
                    message="Invalid email address. Please provide a valid email."
                )

        return api_response(
            status.HTTP_200_OK,
            message='A new verification link has been sent.',
        )

@extend_schema(
    summary='Logout user',
    description="Retrieves and blacklists refresh token from httponly cookie.",
    responses={
        200: envelope_success(
            description='Logged out successfully.'
        ),
    },
)
@method_decorator(csrf_protect, name='dispatch')
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
        if not refresh_token:
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
        res = api_response(status.HTTP_200_OK, message='Logged out successfully.')
        res.delete_cookie(settings.REFRESH_TOKEN_COOKIE_NAME, path='/api/auth/token/refresh/')
        return res

@extend_schema(
    summary='Change email',
    description="Initiates email change and sends verification link to the new email address.",
    request=InitiateEmailChangeSerializer,
    responses={
        200: envelope_success(
            description='A verification link has been sent to the new email address.'
        ),
    },
)
class InitiateEmailChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = InitiateEmailChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_email = serializer.validated_data['new_email']
        password = serializer.validated_data['password']

        service = AccountService()
        try:
            user_idb64, token = service.initiate_email_change(request.user, new_email, password)
        except ValueError as e:
            return api_response(status.HTTP_400_BAD_REQUEST, message=str(e))

        # Send verification email to new email
        EmailService().send_email_change_verification(new_email, user_idb64, token, request.user.name)
        return api_response(status.HTTP_200_OK, message='A verification email has been sent to the new address.')


@extend_schema(
    summary='Confirm email change',
    description="Confirm new email of user.",
    request=ConfirmEmailChangeSerializer,
    responses={
        200: envelope_success(
            description='Email address updated successfully.'
        ),
    },
)
class ConfirmEmailChangeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ConfirmEmailChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_idb64 = serializer.validated_data['user_id']
        token = serializer.validated_data['token']

        success = AccountService().confirm_email_change(user_idb64, token)
        if success:
            user, old_email = success
            EmailService().send_email_change_notification(old_email, user.email, user.name)
            return api_response(
                status.HTTP_200_OK,
                message='Email address updated successfully.',
            )
        return api_response(
            status.HTTP_400_BAD_REQUEST,
            message='Invalid or expired verification link.',
        )

@extend_schema(
    summary='Delete account',
    description="Destructive action to permanently delete account from database.",
    request=DeleteAccountSerializer,
    responses={
        200: envelope_success(
            description='Account deleted successfully.'
        ),
    },
)
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