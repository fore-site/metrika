from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from ..models import User
from ..services import AccountService

class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.verify_url = reverse('verify-email')
        self.login_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')
        self.verify_token_url = reverse('token_verify')
        self.password_reset_url = reverse('password-reset')
        self.password_reset_confirm_url = reverse('password-reset-confirm')
        self.password_change_url = reverse('password-change')
        self.resend_verification_url = reverse('resend-verification')
        self.logout_url = reverse('logout')
        self.delete_account_url = reverse('delete-account')
        self.me_url = reverse('me')

        # Sample data
        self.valid_email = 'test@example.com'
        self.valid_password = 'StrongP@ss1'
        self.valid_name = 'Test User'
        self.invalid_email = 'notanemail'
        self.weak_password = 'short'

    # Helper methods
    def register_user(self, email=None, password=None, name=None, expected_status=status.HTTP_201_CREATED):
        """Register a user and return the response."""
        data = {
            'email': email or self.valid_email,
            'password': password or self.valid_password,
            'name': name or self.valid_name,
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, expected_status)
        return response

    def verify_user(self, uid, token, expected_status=status.HTTP_200_OK):
        """Call the verify-email endpoint."""
        data = {'uid': uid, 'token': token}
        response = self.client.post(self.verify_url, data, format='json')
        self.assertEqual(response.status_code, expected_status)
        return response

    def login_user(self, email=None, password=None, expected_status=status.HTTP_200_OK):
        """Login and return tokens."""
        data = {
            'email': email or self.valid_email,
            'password': password or self.valid_password,
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, expected_status)
        return response

    def authenticate(self, access_token):
        """Set the client credentials."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    # Registration Tests
    def test_registration_success_and_email_sent(self):
        response = self.register_user()
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('Registration successful', response.data['message'])
        # Check email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verify your email', mail.outbox[0].subject)
        # User exists but is inactive
        user = User.objects.get(email=self.valid_email)
        self.assertFalse(user.is_active)

    def test_registration_duplicate_email_fails(self):
        self.register_user()  # first registration
        response = self.register_user(expected_status=status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('already exists', response.data['message'])

    def test_registration_weak_password_fails(self):
        response = self.register_user(password='short', expected_status=status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        # Check that errors contain field-level details
        self.assertIsNotNone(response.data.get('errors'))

    def test_registration_invalid_email_fails(self):
        response = self.register_user(email='bademail', expected_status=status.HTTP_400_BAD_REQUEST)

    # Email Verification Tests
    def test_verify_email_success(self):
        self.register_user()
        user = User.objects.get(email=self.valid_email)
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_verify_email_invalid_token_fails(self):
        self.register_user()
        user = User.objects.get(email=self.valid_email)
        uid, _ = AccountService().initiate_email_verification(self.valid_email)
        response = self.verify_user(uid, 'badtoken', expected_status=status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid', response.data['message'])

    def test_verify_email_already_active(self):
        # Register and verify once
        self.register_user()
        user = User.objects.get(email=self.valid_email)
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        # Try again with same token – should fail
        response = self.verify_user(uid, token, expected_status=status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid', response.data['message'])

    # Login Tests
    def test_login_success_after_verification(self):
        self.register_user()
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        response = self.login_user()
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])

    def test_login_inactive_user_fails(self):
        self.register_user()
        response = self.login_user(expected_status=status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['status'], 'error')

    def test_login_wrong_password_fails(self):
        self.register_user()
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        response = self.login_user(password='WrongP@ss1', expected_status=status.HTTP_401_UNAUTHORIZED)

    # Token Refresh & Verify
    def test_token_refresh_works(self):
        self.register_user()
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        login_res = self.login_user()
        refresh = login_res.data['data']['refresh']
        response = self.client.post(self.refresh_url, {'refresh': refresh}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data['data'])

    def test_token_verify_valid(self):
        self.register_user()
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        login_res = self.login_user()
        access = login_res.data['data']['access']
        response = self.client.post(self.verify_token_url, {'token': access}, format='json')
        self.assertEqual(response.status_code, 200)

    # Password Reset Tests
    def test_password_reset_initiate_sends_email(self):
        self.register_user()
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        response = self.client.post(self.password_reset_url, {'email': self.valid_email}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('If that email', response.data['message'])
        self.assertEqual(len(mail.outbox), 2)  # verification + reset

    def test_password_reset_initiate_generic_for_unknown_email(self):
        response = self.client.post(self.password_reset_url, {'email': 'no@user.com'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_confirm_changes_password(self):
        self.register_user()
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        # Initiate reset
        uidb64, reset_token = AccountService().initiate_password_reset(self.valid_email)
        new_password = 'NewStrongP@ss2'
        response = self.client.post(
            self.password_reset_confirm_url,
            {'uid': uidb64, 'token': reset_token, 'new_password': new_password},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        # Login with new password
        login_res = self.login_user(password=new_password)
        self.assertEqual(login_res.status_code, 200)

    def test_password_reset_confirm_invalid_token_fails(self):
        self.register_user()
        response = self.client.post(
            self.password_reset_confirm_url,
            {'uid': 'invalid', 'token': 'invalid', 'new_password': 'NewPass1!'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    # Password Change (Authenticated) Tests
    def test_password_change_success(self):
        self.register_user()
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])
        response = self.client.post(
            self.password_change_url,
            {'current_password': self.valid_password, 'new_password': 'NewStrongP@ss2'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)

    def test_password_change_wrong_current_fails(self):
        # ... setup ...
        response = self.client.post(
            self.password_change_url,
            {'current_password': 'wrong', 'new_password': 'NewP@ss1'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_password_change_requires_auth(self):
        response = self.client.post(self.password_change_url, {}, format='json')
        self.assertEqual(response.status_code, 401)

    # Resend Verification Tests
    def test_resend_verification_inactive_user_sends_email(self):
        self.register_user()
        response = self.client.post(self.resend_verification_url, {'email': self.valid_email}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('If that email', response.data['message'])
        self.assertEqual(len(mail.outbox), 2)  # original + resend

    def test_resend_verification_already_active_generic(self):
        self.register_user()
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        response = self.client.post(self.resend_verification_url, {'email': self.valid_email}, format='json')
        self.assertEqual(response.status_code, 200)
        # No extra email
        self.assertEqual(len(mail.outbox), 1)  # original only

    # Logout (Blacklist) Tests
    def test_logout_invalidates_refresh(self):
        self.register_user()
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        login_res = self.login_user()
        refresh = login_res.data['data']['refresh']
        self.authenticate(login_res.data['data']['access'])
        response = self.client.post(self.logout_url, {'refresh': refresh}, format='json')
        self.assertEqual(response.status_code, 200)
        # Refresh token should now be blacklisted
        refresh_fail = self.client.post(self.refresh_url, {'refresh': refresh}, format='json')
        self.assertEqual(refresh_fail.status_code, 401)

    def test_logout_missing_refresh_fails(self):
        self.register_user()
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])
        response = self.client.post(self.logout_url, {}, format='json')
        self.assertEqual(response.status_code, 400)

    # ------------------------------------------------------------------
    # Account Deletion Tests
    # ------------------------------------------------------------------
    def test_delete_account_success(self):
        self.register_user()
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])
        response = self.client.post(
            self.delete_account_url,
            {'password': self.valid_password},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email=self.valid_email).exists())

    def test_delete_account_wrong_password_fails(self):
        # ... setup ...
        response = self.client.post(self.delete_account_url, {'password': 'wrong'}, format='json')
        self.assertEqual(response.status_code, 400)

    # Me Endpoint
    def test_me_authenticated_returns_user(self):
        self.register_user()
        uid, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(uid, token)
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['email'], self.valid_email)
        self.assertIn('name', response.data['data'])

    def test_me_unauthenticated_fails(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 401)

    def test_registration_name_validation(self):
        valid_cases = [
            ('   John   Doe   ', 'John Doe'),
            ("O'Brien", "O'Brien"),
            ("Jean-Pierre", "Jean-Pierre"),
            ("Maria Clara, Jr.", "Maria Clara, Jr."),
            ("André Müller", "André Müller"),
            ("John Smith III", "John Smith III"),
            ("  A B  ", "A B"),
        ]

        for raw, expected in valid_cases:
            with self.subTest(raw=raw):
                response = self.register_user(name=raw)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                user = User.objects.get(email=self.valid_email)
                self.assertEqual(user.name, expected)
                # Clean up for next iteration
                user.delete()

        invalid_cases = [
            '',
            '   ',
            'A',
            '<script>alert(1)</script>',
            '  -John',
            'John-',
            '!@#$%^&*()',
            'name\twith\ttabs',
            '1Jhon,'
            'Jhon2',
        ]

        for bad in invalid_cases:
            with self.subTest(bad=bad):
                # use a fresh email to avoid duplicate errors
                email = f'badname_{hash(bad)}@test.com'
                response = self.client.post(
                    self.register_url,
                    {'email': email, 'password': self.valid_password, 'name': bad},
                    format='json'
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIsNotNone(response.data.get('errors'))