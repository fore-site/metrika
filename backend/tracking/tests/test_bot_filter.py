from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import User
from sites.models import Site
from tracking.models import Event

class BotFilteringTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user = User.objects.create_user(email='x@y.com', password='p', name='X')
        self.site = Site.objects.create(user=user, domain='example.com')
        self.url = reverse('track-event')
        self.valid_payload = {
            'visitor_id': '550e8400-e29b-41d4-a716-446655440000',
            'url': 'https://example.com/page',
        }
        self.headers = {'HTTP_X_TRACKING_TOKEN': self.site.tracking_token}

    def test_googlebot_is_filtered(self):
        res = self.client.post(
            self.url,
            self.valid_payload,
            format='json',
            HTTP_USER_AGENT='Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            **self.headers
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(Event.objects.count(), 0)

    def test_regular_user_agent_is_not_filtered(self):
        res = self.client.post(
            self.url,
            self.valid_payload,
            format='json',
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            **self.headers
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(Event.objects.count(), 1)

    def test_empty_user_agent_is_not_filtered(self):
        res = self.client.post(
            self.url,
            self.valid_payload,
            format='json',
            HTTP_USER_AGENT='',
            **self.headers
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(Event.objects.count(), 1)