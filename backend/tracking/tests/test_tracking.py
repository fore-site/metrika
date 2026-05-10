from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from sites.models import Site
from tracking.models import Event

class EventIngestionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user = User.objects.create_user(email='t@x.com', password='x', name='T')
        cls.site = Site.objects.create(user=cls.user, domain='example.com')
        cls.url = reverse('track-event')
        cls.headers = {'HTTP_X_TRACKING_TOKEN': cls.site.tracking_token}
        cls.valid_payload = {
            'visitor_id': '550e8400-e29b-41d4-a716-446655440000',
            'url': 'https://example.com/page',
            'referrer': 'https://www.google.com/search?q=test',
            'timezone': 'Europe/London',
        }

    def _mock_geolocate(self):
        return {
            'country': 'United Kingdom',
            'region': 'England',
            'city': 'London',
            'continent': 'Europe',
        }

    @patch('tracking.services.geolocate')
    def test_valid_event_returns_200_and_stores_all_fields(self, mock_geo):
        mock_geo.return_value = self._mock_geolocate()

        res = self.client.post(
            self.url, self.valid_payload,
            format='json',
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            REMOTE_ADDR='81.2.69.144',
            **self.headers,
        )
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        event = Event.objects.first()
        self.assertIsNotNone(event)
        self.assertEqual(event.site, self.site)
        self.assertEqual(event.visitor_id, self.valid_payload['visitor_id'])
        self.assertEqual(event.url, self.valid_payload['url'])
        self.assertEqual(event.referrer, self.valid_payload['referrer'])
        self.assertEqual(event.timezone, 'Europe/London')

        # Geolocation fields
        self.assertEqual(event.country, 'United Kingdom')
        self.assertEqual(event.region, 'England')
        self.assertEqual(event.city, 'London')

        # User-agent parsed fields
        # self.assertEqual(event.browser, 'Mozilla')
        self.assertEqual(event.os, 'Windows')
        self.assertEqual(event.device_type, 'desktop')

        # Source/medium from Google organic
        self.assertEqual(event.source, 'Google')
        self.assertEqual(event.medium, 'organic')

        # IP
        self.assertEqual(event.ip_address, '81.2.69.144')

    # Missing token
    def test_missing_token_returns_401(self):
        res = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # Invalid token
    def test_invalid_token_returns_401(self):
        headers = {'HTTP_X_TRACKING_TOKEN': 'badtoken'}
        res = self.client.post(self.url, self.valid_payload, format='json', headers=headers)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # Inactive site
    def test_inactive_site_rejected(self):
        self.site.is_active = False
        self.site.save()
        res = self.client.post(self.url, self.valid_payload, format='json', **self.headers)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # URL domain mismatch
    @patch('tracking.services.geolocate')
    def test_url_domain_mismatch_returns_400(self, mock_geo):
        mock_geo.return_value = self._mock_geolocate()
        payload = {**self.valid_payload, 'url': 'https://other.com/page'}
        res = self.client.post(self.url, payload, format='json', **self.headers)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # Payload validation errors
    def test_missing_url_returns_400(self):
        payload = {**self.valid_payload, 'url': ''}
        res = self.client.post(self.url, payload, format='json', **self.headers)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_url_returns_400(self):
        payload = {**self.valid_payload, 'url': 'not-a-url'}
        res = self.client.post(self.url, payload, format='json', **self.headers)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # Source/medium parsing scenarios
    @patch('tracking.services.geolocate')
    def test_direct_visit_no_referrer(self, mock_geo):
        mock_geo.return_value = self._mock_geolocate()
        payload = {**self.valid_payload, 'referrer': ''}
        res = self.client.post(self.url, payload, format='json', **self.headers)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        event = Event.objects.order_by('-timestamp').first()
        self.assertEqual(event.source, 'Direct')
        self.assertEqual(event.medium, 'none')

    @patch('tracking.services.geolocate')
    def test_social_referrer_facebook(self, mock_geo):
        mock_geo.return_value = self._mock_geolocate()
        payload = {**self.valid_payload, 'referrer': 'https://www.facebook.com/somepost'}
        res = self.client.post(self.url, payload, format='json', **self.headers)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        event = Event.objects.order_by('-timestamp').first()
        self.assertEqual(event.source, 'Facebook')
        self.assertEqual(event.medium, 'social')

    @patch('tracking.services.geolocate')
    def test_referral_from_unknown_domain(self, mock_geo):
        mock_geo.return_value = self._mock_geolocate()
        payload = {**self.valid_payload, 'referrer': 'https://blog.example.org/article'}
        res = self.client.post(self.url, payload, format='json', **self.headers)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        event = Event.objects.order_by('-timestamp').first()
        self.assertEqual(event.source, 'blog.example.org')
        self.assertEqual(event.medium, 'referral')

    # Edge: valid subdomain allowed
    @patch('tracking.services.geolocate')
    def test_subdomain_url_allowed(self, mock_geo):
        mock_geo.return_value = self._mock_geolocate()
        payload = {**self.valid_payload, 'url': 'https://blog.example.com/post'}
        res = self.client.post(self.url, payload, format='json', **self.headers)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    @patch('tracking.services.geolocate')
    def test_root_domain_allowed(self, mock_geo):
        mock_geo.return_value = self._mock_geolocate()
        payload = {**self.valid_payload, 'url': 'https://example.com/page'}
        res = self.client.post(self.url, payload, format='json', **self.headers)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    @patch('tracking.services.geolocate')
    def test_false_domain_disallowed(self, mock_geo):
        mock_geo.return_value = self._mock_geolocate()
        payload = {**self.valid_payload, 'url': 'https://myexample.com/page'}
        res = self.client.post(self.url, payload, format='json', **self.headers)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)