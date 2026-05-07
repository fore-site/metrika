from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from ..models import User, LoginAttempt
from ..services import AccountService

class LoginSuspicionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='detect@example.com',
            password='StrongP@ss1',
            name='Detective'
        )
        cls.service = AccountService()
        cls.old_date = timezone.now() - timedelta(days=31)
        cls.recent_date = timezone.now() - timedelta(days=5)


    def _create_attempt(self, ip, ua, success=True, timestamp=None):
        LoginAttempt.objects.create(
            user=self.user,
            email=self.user.email,
            ip_address=ip,
            user_agent=ua,
            was_successful=success,
            timestamp=timestamp or self.recent_date,
        )

    def test_no_prior_successful_logins__not_suspicious(self):
        # No login attempts at all
        self.assertFalse(
            self.service.detect_suspicious_login(self.user, '1.1.1.1')
        )

    def test_only_failed_logins__not_suspicious(self):
        self._create_attempt('1.1.1.1', 'ua1', success=False)
        self.assertFalse(
            self.service.detect_suspicious_login(self.user, '2.2.2.2')
        )

    def test_same_ip__not_suspicious(self):
        self._create_attempt('1.1.1.1', 'ua1', success=True)
        self.assertFalse(
            self.service.detect_suspicious_login(self.user, '1.1.1.1')
        )

    def test_new_ip__suspicious(self):
        self._create_attempt('1.1.1.1', 'ua1', success=True)
        self.assertTrue(
            self.service.detect_suspicious_login(self.user, '2.2.2.2')
        )

    def test_only_old_successful_logins_ignored__not_suspicious(self):
        """Successful logins older than 30 days are ignored."""
        self._create_attempt('1.1.1.1', 'ua1', success=True, timestamp=self.old_date)

        self.assertFalse(
            self.service.detect_suspicious_login(self.user, '2.2.2.2')
        )
        

    def test_mixed_recent_and_old__new_ip_against_recent_is_suspicious(self):
        self._create_attempt('1.1.1.1', 'ua1', success=True, timestamp=self.old_date)
        self._create_attempt('2.2.2.2', 'ua1', success=True, timestamp=self.recent_date)

        self.assertTrue(
            self.service.detect_suspicious_login(self.user, '3.3.3.3')
        )
