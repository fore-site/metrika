from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from sites.models import Site
from sites.services import SiteService


class SiteModelTests(TestCase):
    def test_tracking_token_auto_generated(self):
        user = User.objects.create_user(email='a@b.com', password='x')
        site = Site.objects.create(user=user, domain='example.com')
        self.assertIsNotNone(site.tracking_token)
        self.assertEqual(len(site.tracking_token), 32)   # uuid4 hex

    def test_tracking_token_unique(self):
        user = User.objects.create_user(email='a@b.com', password='x')
        s1 = Site.objects.create(user=user, domain='a.com')
        s2 = Site.objects.create(user=user, domain='b.com')
        self.assertNotEqual(s1.tracking_token, s2.tracking_token)

    def test_domain_user_unique_together(self):
        user = User.objects.create_user(email='a@b.com', password='x')
        Site.objects.create(user=user, domain='example.com')
        with self.assertRaises(Exception):
            Site.objects.create(user=user, domain='example.com')

    def test_site_str(self):
        user = User.objects.create_user(email='a@b.com', password='x')
        site = Site.objects.create(user=user, domain='example.com')
        self.assertIn('example.com', str(site))
        self.assertIn('a@b.com', str(site))


class SiteServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='a@b.com', password='x')
        self.other = User.objects.create_user(email='c@d.com', password='x')
        self.service = SiteService()

    def test_create_site_duplicate_raises(self):
        self.service.create_site(self.user.id, 'example.com')
        with self.assertRaises(ValueError):
            self.service.create_site(self.user.id, 'example.com')

    def test_get_sites_for_user_only_active(self):
        self.service.create_site(self.user.id, 'one.com')
        s2 = self.service.create_site(self.user.id, 'two.com')
        self.service.deactivate_site(s2.id, self.user.id)
        sites = self.service.get_sites_for_user(self.user.id)
        self.assertEqual(sites.count(), 1)
        self.assertEqual(sites.first().domain, 'one.com')

    def test_get_site_by_token(self):
        site = self.service.create_site(self.user.id, 'ex.com')
        found = self.service.get_site_by_token(site.tracking_token)
        self.assertEqual(found, site)

    def test_get_site_by_token_inactive_returns_none(self):
        site = self.service.create_site(self.user.id, 'ex.com')
        self.service.deactivate_site(site.id, self.user.id)
        self.assertIsNone(self.service.get_site_by_token(site.tracking_token))

    def test_update_site_domain(self):
        site = self.service.create_site(self.user.id, 'old.com')
        updated = self.service.update_site(site.id, self.user.id, domain='new.com')
        self.assertEqual(updated.domain, 'new.com')

    def test_update_site_domain_duplicate_raises(self):
        self.service.create_site(self.user.id, 'one.com')
        site = self.service.create_site(self.user.id, 'two.com')
        with self.assertRaises(ValueError):
            self.service.update_site(site.id, self.user.id, domain='one.com')

    def test_update_site_not_owner_returns_none(self):
        site = self.service.create_site(self.user.id, 'ex.com')
        self.assertIsNone(self.service.update_site(site.id, self.other.id, domain='x.com'))

    def test_deactivate_site(self):
        site = self.service.create_site(self.user.id, 'ex.com')
        self.assertTrue(self.service.deactivate_site(site.id, self.user.id))
        site.refresh_from_db()
        self.assertFalse(site.is_active)

    def test_deactivate_site_not_owner_returns_false(self):
        site = self.service.create_site(self.user.id, 'ex.com')
        self.assertFalse(self.service.deactivate_site(site.id, self.other.id))


class SiteAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='a@b.com', password='testpass', name='T')
        self.user.is_active = True
        self.user.save()
        # Obtain token
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.access = str(refresh.access_token)
        self.auth_header = f'Bearer {self.access}'
        self.list_url = reverse('site-list')
        # Detail URL factory
        self.detail_url = lambda sid: reverse('site-detail', kwargs={'public_id': sid})

    def _create_site(self, domain='example.com'):
        return self.client.post(
            self.list_url,
            {'domain': domain},
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )

    # List / Create
    def test_list_empty(self):
        res = self.client.get(self.list_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['data'], [])

    def test_create_site_success(self):
        res = self._create_site('  Example.COM/  ')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['data']['domain'], 'example.com')
        self.assertIn('tracking_token', res.data['data'])
        self.assertEqual(len(res.data['data']['tracking_token']), 32)

    def test_create_duplicate_domain_fails(self):
        self._create_site('example.com')
        res = self._create_site('example.com')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_invalid_domain_fails(self):
        res = self._create_site('http://example.com')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_shows_only_user_sites(self):
        self._create_site('mine.com')
        # Create another user's site
        other = User.objects.create_user(email='x@y.com', password='x', name='X')
        other_site = Site.objects.create(user=other, domain='theirs.com')
        res = self.client.get(self.list_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        domains = [s['domain'] for s in res.data['data']]
        self.assertIn('mine.com', domains)
        self.assertNotIn('theirs.com', domains)

    # Detail: retrieve, update, delete
    def test_retrieve_own_site(self):
        create_res = self._create_site('own.com')
        sid = create_res.data['data']['public_id']
        res = self.client.get(self.detail_url(sid), HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['data']['domain'], 'own.com')

    def test_retrieve_other_user_site_returns_404(self):
        other = User.objects.create_user(email='x@y.com', password='x', name='X')
        site = Site.objects.create(user=other, domain='theirs.com')
        res = self.client.get(self.detail_url(site.public_id), HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_domain(self):
        create_res = self._create_site('old.com')
        sid = create_res.data['data']['public_id']
        res = self.client.put(
            self.detail_url(sid),
            {'domain': 'new.com'},
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['data']['domain'], 'new.com')

    def test_update_domain_duplicate_fails(self):
        self._create_site('one.com')
        two = self._create_site('two.com').data['data']['public_id']
        res = self.client.put(
            self.detail_url(two),
            {'domain': 'one.com'},
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_soft_delete(self):
        create_res = self._create_site('bye.com')
        sid = create_res.data['data']['public_id']
        res = self.client.delete(self.detail_url(sid), HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        # The site should no longer appear in list
        list_res = self.client.get(self.list_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(list_res.data['data'], [])
        # But still exists in DB
        site = Site.objects.get(public_id=sid)
        self.assertFalse(site.is_active)

    def test_unauthenticated_requests_return_401(self):
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)