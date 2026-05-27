from django.test import TestCase
from django.urls import reverse
from rest_framework import status

class TrackingRateLimitTest(TestCase):
    def setUp(self):
        # create a site and token
        self.url = reverse('login')
        self.payload = {'email': 'testmail',
                        'password': 'test@password',
                        'name': 'Test Name',}

    def test_login_throttle(self):
        for _ in range(10):
            res = self.client.post(self.url, self.payload, format='json',)
        # The last request should be 429
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('throttled', res.data['errors'][0]['code'])