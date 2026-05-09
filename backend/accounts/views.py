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
from rest_framework_simplejwt.exceptions import AuthenticationFailed, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from common.response import api_response
from email_service.services import EmailService
from .services import AccountService
from .serializers import (
    NameChangeSerializer,
    InitiateEmailChangeSerializer,
    ConfirmEmailChangeSerializer,
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    TokenObtainPairSerializer,
    VerifyEmailSerializer,
    UserSerializer,
    DeleteAccountSerializer,
    PasswordChangeSerializer,
    ResendVerificationSerializer,
)
from drf_spectacular.utils import extend_schema
from common.openapi import envelope_success
import logging 

logger = logging.getLogger(__name__)

@extend_schema(
    summary='Register a new user',
    description='Creates an inactive user and sends a verification email.',
    request=RegisterSerializer,
    responses=envelope_success,
)
class RegisterView(generics.CreateAPIView):
    permission_classes = []
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        name = serializer.validated_data['name']

        try:
            AccountService().create_user(email, name, password)
        except ValueError as e:
            return api_response(
                status.HTTP_400_BAD_REQUEST,
                message=str(e),
            )

        # Send verification email
        result = AccountService().initiate_email_verification(email)
        if result:
            user_idb64, token = result
            EmailService().send_verification_email(email, user_idb64, token, name=name)
            
            return api_response(
                status.HTTP_201_CREATED,
                message='Registration successful. Kindly check your email to verify your account.',
            )

@extend_schema(
    summary='Verify email after registration',
    description="Validate (user_id, token) and sets a registered user's inactive status to active.",
    request=VerifyEmailSerializer,
    responses=envelope_success,
)
class VerifyEmailView(APIView):
    permission_classes = []

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
    request=TokenObtainPairSerializer,
    responses=envelope_success,
)
class LoginView(BaseLoginView):
    serializer_class = CustomTokenObtainPairSerializer
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
        except AuthenticationFailed:
            email = request.data.get('email', '')
            user_agent = AccountService().get_user_agent(request)
            ip_address = AccountService().get_client_ip(request)
            user = AccountService().get_user_by_email(email)
            if user:
                AccountService().record_login_attempt(
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    was_successful=False,
                    user=user
                )
            raise

        if response.status_code == 200:
            email = request.data.get('email', '')
            user_agent = AccountService().get_user_agent(request)
            ip_address = AccountService().get_client_ip(request)
            user = AccountService().get_user_by_email(email)
            # Record login attempt
            AccountService().record_login_attempt(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                was_successful=True,
                user=user
            )

            # Check if login was suspicious
            if AccountService().detect_suspicious_login(user, ip_address):
                EmailService().send_suspicious_login_notification(user, ip_address, user_agent)

            refresh_token = response.data['refresh']
            data = {'access': response.data['access']}
            print(refresh_token)
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
                path='/api/auth/',  # Only send cookie to the api/auth endpoint
            )

            get_token(request._request)  # Ensure CSRF token is set in the response cookies
            return res
        return response

@extend_schema(
    summary='Obtain new access token',
    description="Uses the refresh token from httpOnly cookie to obtain and return an access token in the body.",
    request=None,  # No request body needed since refresh token is in cookie
    responses=envelope_success,
)
@method_decorator(csrf_protect, name='dispatch')
class TokenRefreshView(BaseRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
        if not refresh_token:
                return api_response(
                    status.HTTP_400_BAD_REQUEST,
                    message='Refresh token is required.',
                )

        try:
            old_refresh = RefreshToken(refresh_token)
            old_refresh.check_blacklist()

        except TokenError:
            return api_response(
                status.HTTP_400_BAD_REQUEST,
                message='Invalid or expired refresh token.',
            )
        old_refresh.blacklist()
        user_id = old_refresh.get('user_id')
        user = AccountService().get_user_by_id(user_id)
        if not user.is_active or user.is_suspended:
            logger.warning(f"Inactive or suspended user attempted token refresh: {user.email}")
            return api_response(
                status.HTTP_400_BAD_REQUEST,
                message='No active account found for the provided credentials.',
            )
        new_refresh = RefreshToken.for_user(user)

        res = api_response(
            status.HTTP_200_OK,
            data={'access': str(new_refresh.access_token)},
            message='Token refreshed successfully.',
        )
        res.set_cookie(
            key=settings.REFRESH_TOKEN_COOKIE_NAME,
            value=str(new_refresh),
            httponly=settings.REFRESH_TOKEN_COOKIE_HTTPONLY,
            max_age=settings.REFRESH_TOKEN_MAX_AGE,
            samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
            path='/api/auth/',
        )
        return res


@extend_schema(
    summary='Verify JWT token validity',
    description="Verifies if a JWT token is valid.",
    responses=envelope_success,
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
    responses=envelope_success,
)
class PasswordResetView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        result = AccountService().initiate_password_reset(email)
        if result:
            user = AccountService().get_user_by_email(email)
            name = user.name if user else ''
            user_idb64, token = result
            EmailService().send_password_reset_email(email, user_idb64, token, name=name)
            
            return api_response(
                status.HTTP_200_OK,
                message='A password reset link has been sent.',
            )
        return api_response(
            status.HTTP_400_BAD_REQUEST,
            message="Invalid email address. Please provide a valid email"
        )

@extend_schema(
    summary='Confirm password reset',
    description="Validates (user_id, token, new_password) and sets user's new password in database.",
    request=PasswordResetConfirmSerializer,
    responses=envelope_success,
)
class PasswordResetConfirmView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_idb64 = serializer.validated_data['user_id']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        user = AccountService().confirm_password_reset(user_idb64, token, new_password)
        if user:

            # Invalidate all existing tokens for the user after password reset
            for outstanding in OutstandingToken.objects.filter(user=user):
                if not BlacklistedToken.objects.filter(token=outstanding).exists():
                    BlacklistedToken.objects.create(token=outstanding)

            return api_response(
                status.HTTP_200_OK,
                message='Password has been reset successfully. Kindly login again',
            )
        return api_response(
            status.HTTP_400_BAD_REQUEST,
            message='Invalid or expired reset token.',
        )

@extend_schema(
    methods=['GET'],
    summary='View user profile',
    description="Returns user's current detail.",
    responses=envelope_success,
)
@extend_schema(
    methods=['PATCH'],
    summary='Update user profile',
    description="Updates user's current detail.",
    request=NameChangeSerializer,
    responses=envelope_success,
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
    responses=envelope_success,
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
        for outstanding in OutstandingToken.objects.filter(user=user):
            if not BlacklistedToken.objects.filter(token=outstanding).exists():
                BlacklistedToken.objects.create(token=outstanding)

        # rotate refresh token
        new_refresh = RefreshToken.for_user(user)

        res = api_response(
            status.HTTP_200_OK, 
            message='Password changed successfully.')
        res.set_cookie(
            key=settings.REFRESH_TOKEN_COOKIE_NAME,
            value=str(new_refresh),
            httponly=settings.REFRESH_TOKEN_COOKIE_HTTPONLY,
            max_age=settings.REFRESH_TOKEN_MAX_AGE,
            samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
            path='/api/auth/',
        )
        return res

@extend_schema(
    summary='Resend email verification link',
    description="Resends a newly generated email verification link to the user's email.",
    request=ResendVerificationSerializer,
    responses=envelope_success,
)
class ResendVerificationView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        result = AccountService().resend_verification(email)
        if result:
            user = AccountService().get_user_by_email(email)
            name = user.name if user else ''
            user_idb64, token = result
            EmailService().send_verification_email(email, user_idb64, token, name=name)
            
            return api_response(
                status.HTTP_200_OK,
                message='A new verification link has been sent.',
            )
        return api_response(
            status.HTTP_400_BAD_REQUEST,
            message="User with email does not exist or already verified."
        )

@extend_schema(
    summary='Logout user',
    description="Retrieves and blacklists refresh token from httponly cookie.",
    request=None,
    responses=envelope_success,
)
@method_decorator(csrf_protect, name='dispatch')
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
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
        res.delete_cookie(settings.REFRESH_TOKEN_COOKIE_NAME, path='/api/auth/')
        return res

@extend_schema(
    summary='Change email',
    description="Initiates email change and sends verification link to the new email address.",
    request=InitiateEmailChangeSerializer,
    responses=envelope_success,
)
class InitiateEmailChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = InitiateEmailChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_email = serializer.validated_data['new_email']
        password = serializer.validated_data['password']

        try:
            user_idb64, token = AccountService().initiate_email_change(request.user, new_email, password)
        except ValueError as e:
            return api_response(status.HTTP_400_BAD_REQUEST, message=str(e))

        # Send verification email to new email
        EmailService().send_email_change_verification(new_email, user_idb64, token, request.user.name)
        return api_response(status.HTTP_200_OK, message='A verification link has been sent to the new email address.')


@extend_schema(
    summary='Confirm email change',
    description="Validate (user_id, token) and update new email of user in database.",
    request=ConfirmEmailChangeSerializer,
    responses=envelope_success,
)
class ConfirmEmailChangeView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ConfirmEmailChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_idb64 = serializer.validated_data['user_id']
        token = serializer.validated_data['token']

        success = AccountService().confirm_email_change(user_idb64, token)
        if success:
            user, old_email = success

            # Invalidate all existing tokens for the user after password change
            for outstanding in OutstandingToken.objects.filter(user=user):
                if not BlacklistedToken.objects.filter(token=outstanding).exists():
                    BlacklistedToken.objects.create(token=outstanding)
                
            # rotate refresh token
            new_refresh = RefreshToken.for_user(user)

            EmailService().send_email_change_notification(old_email, user.email, user.name)
            
            res = api_response(
            status.HTTP_200_OK, 
            message='Password changed successfully.'
            )
        
            res.set_cookie(
                key=settings.REFRESH_TOKEN_COOKIE_NAME,
                value=str(new_refresh),
                httponly=settings.REFRESH_TOKEN_COOKIE_HTTPONLY,
                max_age=settings.REFRESH_TOKEN_MAX_AGE,
                samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
                path='/api/auth/',
            )
            return res
        return api_response(
            status.HTTP_400_BAD_REQUEST,
            message='Invalid or expired verification link.',
        )

@extend_schema(
    summary='Delete account',
    description="Destructive action to permanently delete account from database.",
    request=DeleteAccountSerializer,
    responses=envelope_success,
)
class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        
        # Delete all associated jwt tokens
        outstanding_tokens = OutstandingToken.objects.filter(user=user)
        if outstanding_tokens:
            for outstanding in outstanding_tokens:
                blacklisted = BlacklistedToken.objects.filter(token=outstanding)
                if blacklisted:
                    blacklisted.delete()
            outstanding_tokens.delete()

        success = AccountService().delete_account(user, serializer.validated_data['password'])

        if not success:
            return api_response(
                status.HTTP_400_BAD_REQUEST,
                message='Password is incorrect.',
            )
        
        res = api_response(status.HTTP_200_OK, message='Account deleted successfully.')
        res.delete_cookie(settings.REFRESH_TOKEN_COOKIE_NAME, path='/api/auth/')
        return res