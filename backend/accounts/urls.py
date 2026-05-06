from django.urls import path
from .views import (
    InitiateEmailChangeView,
    ConfirmEmailChangeView,
    RegisterView,
    VerifyEmailView,
    LoginView,
    TokenRefreshView,
    TokenVerifyView,
    PasswordResetView,
    PasswordResetConfirmView,
    MeView,
    ResendVerificationView,
    LogoutView,
    PasswordChangeView,
    DeleteAccountView,
)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password-change/', PasswordChangeView.as_view(), name='password-change'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete-account'),
    path('email-change/', InitiateEmailChangeView.as_view(), name='email-change'),
    path('email-change/confirm/', ConfirmEmailChangeView.as_view(), name='email-change-confirm'),
    path('me/', MeView.as_view(), name='me'),
]