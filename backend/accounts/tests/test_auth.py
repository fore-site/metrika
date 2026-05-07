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
        self.login_url = reverse('login')
        self.refresh_url = reverse('token_refresh')
        self.verify_token_url = reverse('token_verify')
        self.password_reset_url = reverse('password-reset')
        self.password_reset_confirm_url = reverse('password-reset-confirm')
        self.password_change_url = reverse('password-change')
        self.resend_verification_url = reverse('resend-verification')
        self.logout_url = reverse('logout')
        self.delete_account_url = reverse('delete-account')
        self.me_url = reverse('me')
        self.email_change = reverse('email-change')
        self.email_change_confirm = reverse('email-change-confirm')

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

    def verify_user(self, user_id, token, expected_status=status.HTTP_200_OK):
        """Call the verify-email endpoint."""
        data = {'user_id': user_id, 'token': token}
        response = self.client.post(self.verify_url, data, format='json')
        self.assertEqual(response.status_code, expected_status)
        return response

    def register_and_verify_user(self):
        """Create user, initiate email verificaion and verify email"""
        AccountService().create_user(self.valid_email, self.valid_name, self.valid_password)
        user_idb64, token = AccountService().initiate_email_verification(self.valid_email)
        result = AccountService().verify_email(user_idb64=user_idb64, token=token)
        self.assertTrue(result)

        user = AccountService().get_user_by_email(self.valid_email)
        self.assertTrue(user.is_active)


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
        self.assertIn('already exists', response.data['message'])

    def test_registration_weak_password_fails(self):
        response = self.register_user(password='short', expected_status=status.HTTP_400_BAD_REQUEST)

        # Check that errors contain field-level details
        self.assertIsNotNone(response.data.get('errors'))

    def test_registration_invalid_email_fails(self):
        response = self.register_user(email='bademail', expected_status=status.HTTP_400_BAD_REQUEST)

        self.assertIn('Validation error', response.data['message'])

    # Email Verification Tests
    def test_verify_email_success(self):
        user = AccountService().create_user(self.valid_email, self.valid_name, self.valid_password)
        user_id, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(user_id, token)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_verify_email_invalid_token_fails(self):
        AccountService().create_user(self.valid_email, self.valid_name, self.valid_password)
        user_id, _ = AccountService().initiate_email_verification(self.valid_email)
        response = self.verify_user(user_id, 'badtoken', expected_status=status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid', response.data['message'])

    def test_verify_email_already_active(self):
        # Register and verify once
        AccountService().create_user(self.valid_email, self.valid_name, self.valid_password)
        user_id, token = AccountService().initiate_email_verification(self.valid_email)
        self.verify_user(user_id, token)
        # Try again with same token – should fail
        self.verify_user(user_id, token)
        user = AccountService().get_user_by_email(self.valid_email)
        self.assertTrue(user.is_active)

    # Login Tests
    def test_login_success_after_verification(self):
        self.register_and_verify_user()
        response = self.login_user()
        self.assertIn('access', response.data['data'])
        self.assertNotIn('refresh', response.data['data'])

    def test_login_inactive_user_fails(self):
        self.register_user()
        self.login_user(expected_status=status.HTTP_401_UNAUTHORIZED)

    def test_login_wrong_password_fails(self):
        self.register_and_verify_user()
        self.login_user(password='WrongP@ss1', expected_status=status.HTTP_401_UNAUTHORIZED)


    def test_token_verify_valid(self):
        self.register_and_verify_user()
        login_res = self.login_user()
    
        access = login_res.data['data']['access']
        response = self.client.post(self.verify_token_url, {'token': access}, format='json')
        self.assertEqual(response.status_code, 200)

    # Password Reset Tests
    def test_password_reset_initiate_sends_email(self):
        self.register_and_verify_user()
        response = self.client.post(self.password_reset_url, {'email': self.valid_email}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('A password reset link', response.data['message'])
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_initiate_generic_for_unknown_email(self):
        response = self.client.post(self.password_reset_url, {'email': 'no@user.com'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_confirm_changes_password(self):
        self.register_and_verify_user()
        # Initiate reset
        user_idb64, reset_token = AccountService().initiate_password_reset(self.valid_email)
        new_password = 'NewStrongP@ss2'
        response = self.client.post(
            self.password_reset_confirm_url,
            {'user_id': user_idb64, 'token': reset_token, 'new_password': new_password},
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
            {'user_id': 'invalid', 'token': 'invalid', 'new_password': 'NewPass1!'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    # Password Change (Authenticated) Tests
    def test_password_change_success(self):
        self.register_and_verify_user()
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])
        response = self.client.post(
            self.password_change_url,
            {'current_password': self.valid_password, 'new_password': 'NewStrongP@ss2'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)

    def test_password_change_wrong_current_fails(self):
        self.register_and_verify_user()
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])
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
        self.assertIn('A new verification link', response.data['message'])
        self.assertEqual(len(mail.outbox), 2)  # original + resend

    def test_resend_verification_already_active_generic(self):
        self.register_and_verify_user()
        response = self.client.post(self.resend_verification_url, {'email': self.valid_email}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('already verified', response.data['message'])
        # No extra email
        self.assertEqual(len(mail.outbox), 0)

    # Account Deletion Tests
    def test_delete_account_success(self):
        self.register_and_verify_user()
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
        self.register_and_verify_user()
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])
        response = self.client.post(self.delete_account_url, {'password': 'wrong'}, format='json')
        self.assertEqual(response.status_code, 400)

    # Me Endpoint
    def test_me_authenticated_returns_user(self):
        self.register_and_verify_user()
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['email'], self.valid_email)
        self.assertIn('name', response.data['data'])

    def test_me_unauthenticated_fails(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 401)

    # Name validation
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
            '!@#$%^&*()',
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


    def test_name_change_success(self):
    # Register, verify, and login
        self.register_and_verify_user()
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])

        # Update name
        response = self.client.patch(self.me_url, {'name': 'New Name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['name'], 'New Name')
        # Database should reflect change
        user = User.objects.get(email=self.valid_email)
        self.assertEqual(user.name, 'New Name')

    def test_name_change_validation_fails(self):
        self.register_and_verify_user()
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])

        invalid_names = [
            '',
            '   ',
            'A',
            '<script>',
        ]
        for bad_name in invalid_names:
            response = self.client.patch(self.me_url, {'name': bad_name}, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_name_change_requires_auth(self):
        # Unauthenticated
        response = self.client.patch(self.me_url, {'name': 'New Name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    
    def test_initiate_email_change_success(self):
        # Setup authenticated user
        self.register_and_verify_user()
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])

        new_email = 'newemail@example.com'
        response = self.client.post(
            self.email_change,
            {'new_email': new_email, 'password': self.valid_password},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify email sent to new address
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Confirm your new email address')
        self.assertEqual(mail.outbox[0].to, [new_email])
        # Old email unchanged
        user = User.objects.get(email=self.valid_email)
        self.assertEqual(user.email, self.valid_email)

    def test_initiate_email_change_wrong_password(self):
        self.register_and_verify_user()
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])

        response = self.client.post(
            self.email_change,
            {'new_email': 'new@example.com', 'password': 'wrongpassword'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Current password is incorrect', response.data['message'])

    def test_initiate_email_change_duplicate_email(self):
        # Create another user to occupy the new email
        other_email = 'other@example.com'
        User.objects.create_user(email=other_email, password='OtherP@ss1', name='Other')

        self.register_and_verify_user()
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])

        response = self.client.post(
            self.email_change,
            {'new_email': other_email, 'password': self.valid_password},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', response.data['message'])

    def test_initiate_email_change_requires_auth(self):
        response = self.client.post(
            self.email_change,
            {'new_email': 'new@example.com', 'password': 'anything'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_confirm_email_change_invalid_token(self):
        self.register_and_verify_user()
        user_idb64, _ = AccountService().initiate_email_change(
            User.objects.get(email=self.valid_email), 'newemail@gmail.com', self.valid_password
        )
        response = self.client.post(
            self.email_change_confirm,
            {'user_id': user_idb64, 'token': 'invalid'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid or expired', response.data['message'])

    def test_confirm_email_change_cache_expired(self):
        
        self.register_and_verify_user()
        login_res = self.login_user()
        self.authenticate(login_res.data['data']['access'])

        new_email = 'newemail@example.com'
        user_idb64, token = AccountService().initiate_email_change(
            User.objects.get(email=self.valid_email), new_email, self.valid_password
        )
        # Clear the cache to simulate expiry
        from django.core.cache import cache
        cache.delete(f"email_change:{User.objects.get(email=self.valid_email).pk}")

        response = self.client.post(
            self.email_change_confirm,
            {'user_id': user_idb64, 'token': token},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid or expired', response.data['message'])