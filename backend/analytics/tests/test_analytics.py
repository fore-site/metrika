from datetime import date, datetime, timedelta, timezone
from freezegun import freeze_time
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone as django_timezone

from accounts.models import User
from sites.models import Site
from tracking.models import Event
from analytics.models import (
    DailySiteStats, 
    DailyPageStats, 
    DailyReferrerStats,
    DailyBrowserStats,
    DailyCountryStats,
    DailyDeviceStats,
    DailyOSStats
    )
from analytics.services import AggregationService, StatsQueryService

TODAY = date(2026, 5, 15)
NOW = datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc)

class AnalyticsTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.email = 'test@example.com'
        cls.password = 'testpass'
        cls.user = User.objects.create_user(
            email='test@example.com', password='testpass', name='Tester'
        )
        cls.user.is_active = True
        cls.user.save()
        cls.site = Site.objects.create(user=cls.user, domain='example.com')
        
        cls.other_email = 'other@example.com'
        cls.other_password = 'otherpass'
        cls.other_user = User.objects.create_user(
            email='other@example.com', password='otherpass', name='Other'
        )
        cls.other_site = Site.objects.create(user=cls.other_user, domain='other.com')
        cls.timeseries_url = reverse('timeseries', kwargs={'site_id': cls.site.id})

    def setUp(self):
        # Freeze time for every test
        self.freezer = freeze_time(NOW)
        self.freezer.start()
        self.addCleanup(self.freezer.stop)
        self.client = APIClient()
        self.auth_client = APIClient()
        # Obtain JWT for main user (must happen after freezing time)
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.access = str(refresh.access_token)
        self.auth_header = f'Bearer {self.access}'
        self.authenticate(self.auth_client, self.access)

    # helpers 

    def authenticate(self, client, access_token):
        """Set the client credentials."""
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    def _create_event(self, *, site, timestamp, visitor_id, url, **kwargs):
        """
        Event.timestamp uses auto_now_add=True, so it ignores provided values.
        For deterministic analytics tests we create, then update the timestamp.
        """
        event = Event.objects.create(
            site=site,
            visitor_id=visitor_id,
            url=url,
            referrer=kwargs.get('referrer', ''),
            source=kwargs.get('source', ''),
            medium=kwargs.get('medium', ''),
            country=kwargs.get('country', ''),
            region=kwargs.get('region', ''),
            city=kwargs.get('city', ''),
            device_type=kwargs.get('device_type', 'desktop'),
            browser=kwargs.get('browser', ''),
            os=kwargs.get('os', ''),
            user_agent='',
            ip_address='',
            timezone='',
        )
        Event.objects.filter(pk=event.pk).update(timestamp=timestamp)
        return event

    def _make_raw_events(self, site, date_, visitor_ids, urls, referrer='', **kwargs):
        """Create raw Event rows for a specific date (date object)."""
        for i, vid in enumerate(visitor_ids):
            ts = datetime.combine(date_, datetime.min.time()) + timedelta(
                hours=i % 24, minutes=15 * (i % 4)
            )
            ts = django_timezone.make_aware(ts, timezone.utc)
            self._create_event(
                site=site,
                timestamp=ts,
                visitor_id=vid,
                url=urls[i % len(urls)],
                referrer=referrer,
                **kwargs,
            )

    def _make_daily_stats(self, site, date_, visitors, pageviews,
                          sessions, single_sessions, duration_seconds,
                          pageviews_in_sessions):
        DailySiteStats.objects.create(
            site=site,
            date=date_,
            visitors=visitors,
            pageviews=pageviews,
            total_visits=sessions,
            single_page_sessions=single_sessions,
            total_duration_seconds=duration_seconds,
            total_pageviews_in_sessions=pageviews_in_sessions,
        )

    def _create_page_stats(self, site, date_, path, visitors, pageviews):
        DailyPageStats.objects.create(site=site, date=date_, url=path,
                                      visitors=visitors, pageviews=pageviews)

    def _create_referrer_stats(self, site, date_, source, medium, visitors, pageviews):
        DailyReferrerStats.objects.create(site=site, date=date_, source=source,
                                          medium=medium, visitors=visitors,
                                          pageviews=pageviews)

    def _create_country_stats(self, site, date_, country, visitors):
        DailyCountryStats.objects.create(site=site, date=date_, country=country,
                                         visitors=visitors)

    def _create_device_stats(self, site, date_, device_type, visitors):
        DailyDeviceStats.objects.create(site=site, date=date_,
                                        device_type=device_type, visitors=visitors)

    def _create_browser_stats(self, site, date_, browser, visitors):
        DailyBrowserStats.objects.create(site=site, date=date_, browser=browser,
                                         visitors=visitors)

    def _create_os_stats(self, site, date_, os, visitors):
        DailyOSStats.objects.create(site=site, date=date_, os=os, visitors=visitors)

class AggregationServiceTests(AnalyticsTestBase):
    def test_aggregate_date_creates_correct_site_stats(self):
        # Create raw events for a past date
        test_date = date(2026, 5, 14)
        self._make_raw_events(
            self.site, test_date,
            visitor_ids=['v1', 'v1', 'v2', 'v3'],
            urls=['/', '/about', '/', '/contact'],
            referrer='https://google.com',
            source='Google', medium='organic',
            country='US', region='California', city='Los Angeles',
            device_type='desktop', browser='Chrome', os='Windows',
        )

        AggregationService().aggregate_date(self.site, test_date)

        # Check DailySiteStats
        stats = DailySiteStats.objects.get(site=self.site, date=test_date)
        self.assertEqual(stats.visitors, 3)          # v1, v2, v3
        self.assertEqual(stats.pageviews, 4)         # 4 events
        self.assertGreater(stats.total_visits, 0)  # should have sessions

        # Check page stats
        pages = DailyPageStats.objects.filter(site=self.site, date=test_date)
        self.assertTrue(pages.filter(url='/').exists())
        self.assertTrue(pages.filter(url='/about').exists())

        # Check referrer stats
        refs = DailyReferrerStats.objects.filter(site=self.site, date=test_date)
        self.assertTrue(refs.filter(source='Google', medium='organic').exists())


class StatsQueryServiceTests(AnalyticsTestBase):
    def setUp(self):
        super().setUp()
        self.service = StatsQueryService()
        # Create pre-aggregated data for several dates
        self._make_daily_stats(self.site, date(2026, 5, 10), 100, 200, 10, 4, 3000, 200)
        self._make_daily_stats(self.site, date(2026, 5, 11), 120, 250, 12, 5, 3600, 250)
        self._make_daily_stats(self.site, date(2026, 5, 12), 130, 270, 13, 6, 3900, 270)
        self._make_daily_stats(self.site, date(2026, 5, 13), 140, 300, 14, 7, 4200, 300)
        self._make_daily_stats(self.site, date(2026, 5, 14), 150, 320, 15, 8, 4500, 320)

    def test_get_timeseries_with_date_range(self):
        data = self.service.get_daily_timeseries(
            self.site.id, date(2026, 5, 10), date(2026, 5, 14)
        )
        self.assertEqual(len(data), 5)   # 5 days
        for point in data:
            self.assertIn('date', point)
            self.assertIn('visitors', point)
            self.assertIn('pageviews', point)
            self.assertIn('bounce_rate', point)
            self.assertIn('avg_duration_seconds', point)
            self.assertIn('views_per_visit', point)

    def test_get_timeseries_session_metrics_calculated(self):
        data = self.service.get_daily_timeseries(
            self.site.id, date(2026, 5, 10), date(2026, 5, 10)
        )
        point = data[0]
        # 10 sessions, 4 bounces -> 40% bounce rate
        self.assertEqual(point['bounce_rate'], 40.0)
        # 3000 total duration seconds / 10 sessions = 300 avg
        self.assertEqual(point['avg_duration_seconds'], 300)
        # 200 pageviews in sessions / 10 sessions = 20 views/visit
        self.assertEqual(point['views_per_visit'], 20.0)

    def test_get_today_timeseries_from_raw_events(self):
        # Create raw events for today
        self._make_raw_events(
            self.site, TODAY,
            visitor_ids=['v1', 'v2', 'v1', 'v3'],
            urls=['/', '/', '/about', '/contact'],
        )
        data = self.service.get_today_timeseries(self.site)
        # One row per hour that has at least one event.
        self.assertEqual(len(data), 4)
        self.assertTrue(all('hour' in p for p in data))
        self.assertEqual(sum(p['pageviews'] for p in data), 4)

    def test_get_hourly_timeseries(self):
        # Create raw events for last 24 hours (over multiple hours)
        start = NOW - timedelta(hours=24)
        for h in range(24):
            ts = start + timedelta(hours=h)
            self._create_event(
                site=self.site,
                timestamp=ts,
                visitor_id=f'v{h%3}',
                url=f'/page{h%5}',
            )
        data = self.service.get_hourly_timeseries(
            self.site.id,
            start.astimezone(timezone.utc),
            NOW.astimezone(timezone.utc),
        )
        self.assertEqual(len(data), 24)
        # each entry has 'hour' and visitors/pageviews

    def test_get_monthly_timeseries(self):
        # Days from May 10-14, all same month, should return one row
        data = self.service.get_monthly_timeseries(
            self.site.id, date(2026, 5, 1), date(2026, 5, 31)
        )
        self.assertEqual(len(data), 1)
        month_data = data[0]
        # Sums across the 5 days
        self.assertEqual(month_data['visitors'], 640)
        self.assertEqual(month_data['pageviews'], 1340)

    def test_get_yearly_timeseries(self):
        data = self.service.get_yearly_timeseries(
            self.site.id, date(2026, 1, 1), date(2026, 12, 31)
        )
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['visitors'], 640)


class TimeseriesAPITests(AnalyticsTestBase):
    def setUp(self):
        super().setUp()
        # Prepopulate stats for past days (May 10-14)
        for d, (v, pv) in enumerate(zip([100,120,130,140,150], [200,250,270,300,320]), start=10):
            self._make_daily_stats(
                self.site, date(2026, 5, d), v, pv,
                sessions=v//10, single_sessions=v//25,
                duration_seconds=v*30, pageviews_in_sessions=pv,
            )
        # Create raw events for today (May 15)
        self._make_raw_events(
            self.site, TODAY,
            visitor_ids=['v1', 'v2', 'v1', 'v3'],
            urls=['/', '/', '/about', '/contact'],
        )

    # auth and ownership
    def test_unauthenticated_returns_401(self):
        res = self.client.get(self.timeseries_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cross_user_site_returns_404(self):
        other_url = reverse('timeseries', kwargs={'site_id': self.other_site.id})
        res = self.auth_client.get(other_url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # default (no params): today
    def test_default_returns_today_data(self):
        res = self.auth_client.get(self.timeseries_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 4)
        self.assertTrue(all('hour' in p for p in data))
        self.assertEqual(sum(p['pageviews'] for p in data), 4)

    # interval=day with specific day
    def test_interval_day_with_past_date(self):
        # For a past day, TimeseriesView returns hourly buckets from raw events.
        self._make_raw_events(
            self.site,
            date(2026, 5, 10),
            visitor_ids=['x1', 'x2', 'x1', 'x3'],
            urls=['/', '/', '/about', '/contact'],
        )
        res = self.auth_client.get(self.timeseries_url, {'interval': 'day', 'day': '2026-05-10'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        self.assertEqual(len(data), 4)
        self.assertTrue(all('hour' in p for p in data))
        self.assertTrue(all('bounce_rate' in p for p in data))

    def test_interval_day_with_today(self):
        res = self.auth_client.get(self.timeseries_url, {'interval': 'day', 'day': TODAY.isoformat()})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        self.assertEqual(len(data), 4)
        self.assertEqual(sum(p['pageviews'] for p in data), 4)

    def test_interval_day_missing_day_param_returns_400(self):
        res = self.auth_client.get(self.timeseries_url, {'interval': 'day'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # interval=24h: hourly data for past 24h
    def test_interval_24h(self):
        # Add some events in the last 24h
        start = NOW - timedelta(hours=24)
        for h in range(24):
            ts = start + timedelta(hours=h)
            self._create_event(
                site=self.site,
                timestamp=ts,
                visitor_id=f'v{h%3}',
                url=f'/page{h%5}',
            )
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        res = self.client.get(
            self.timeseries_url,
            {'interval': '24h'},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        self.assertIsInstance(data, list)

        for point in data:
            self.assertIn('hour', point)
            self.assertIn('visitors', point)
            self.assertIn('pageviews', point)

    # interval=31d: daily points for last 31 completed days
    def test_interval_31d(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        res = self.client.get(
            self.timeseries_url,
            {'interval': '31d'},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        self.assertEqual(len(data), 5)

    # interval=month-to-date (May 1 to yesterday)
    def test_interval_month_to_date(self):
        res = self.client.get(
            self.timeseries_url,
            {'interval': 'month-to-date'},
            HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        # May 1-14: have stats for 10-14, so 5 points
        self.assertEqual(len(data), 5)

    # interval=year-to-date (Jan 1 to yesterday)
    def test_interval_year_to_date(self):
        # test that range is correct
        res = self.client.get(
            self.timeseries_url,
            {'interval': 'year-to-date'},
            HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        # Year-to-date spans >90 days, so granularity auto-switches to monthly.
        self.assertEqual(len(data), 1)
        self.assertIn('month', data[0])
        self.assertEqual(data[0]['visitors'], 640)

    # interval=custom with start/end
    def test_interval_custom(self):
        res = self.client.get(
            self.timeseries_url,
            {'interval': 'custom', 'start': '2026-05-11', 'end': '2026-05-13'},
            HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        self.assertEqual(len(data), 3)   # 11,12,13
        dates = [p['date'].isoformat() if hasattr(p['date'], 'isoformat') else p['date'] for p in data]
        self.assertEqual(dates, ['2026-05-11', '2026-05-12', '2026-05-13'])

    def test_invalid_interval_returns_400(self):
        res = self.client.get(
            self.timeseries_url,
            {'interval': 'bogus'},
            HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

class SummaryViewTests(AnalyticsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('summary', kwargs={'site_id': self.site.id})
        # Prepopulate daily stats for last 30 days, but create 2 days for testing
        self._make_daily_stats(self.site, date(2026, 5, 10), 100, 200, 10, 4, 3000, 200)
        self._make_daily_stats(self.site, date(2026, 5, 11), 120, 250, 12, 5, 3600, 250)

    def test_unauthenticated_returns_401(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cross_user_returns_404(self):
        other_url = reverse('summary', kwargs={'site_id': self.other_site.id})
        res = self.auth_client.get(other_url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_default_date_range(self):
        """Custom date range sums DailySiteStats."""
        res = self.auth_client.get(self.url, {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        # Should have sum of both days
        self.assertEqual(data['visitors'], 220)
        self.assertEqual(data['pageviews'], 450)

    def test_custom_date_range(self):
        res = self.auth_client.get(self.url, {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-10'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        self.assertEqual(data['visitors'], 100)

    def test_returns_session_metrics(self):
        res = self.auth_client.get(self.url, {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11'})
        data = res.data['data']
        self.assertIn('bounce_rate', data)
        self.assertIn('avg_duration_seconds', data)
        self.assertIn('views_per_visit', data)
        # bounce_rate = total single_page_sessions / total sessions * 100
        # (4+5) / (10+12) * 100 = 9/22*100 ≈ 40.9 -> rounded to nearest int
        self.assertEqual(data['bounce_rate'], 41)

class TopPagesViewTests(AnalyticsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('top-pages', kwargs={'site_id': self.site.id})
        # Create page stats for 2 days, enough rows to exercise pagination.
        for day in [date(2026, 5, 10), date(2026, 5, 11)]:
            # Make "/" deterministically the top page.
            self._create_page_stats(self.site, day, '/', visitors=100, pageviews=1000)
            # 59 additional unique pages (total unique urls = 60).
            for i in range(59):
                self._create_page_stats(self.site, day, f'/page-{i}', visitors=1, pageviews=10)

    def test_unauthenticated_returns_401(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cross_user_returns_404(self):
        other_url = reverse('top-pages', kwargs={'site_id': self.other_site.id})
        res = self.auth_client.get(other_url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_returns_top_pages(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11'},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)
        # First entry should be '/' with most pageviews.
        top = data[0]
        self.assertEqual(top['url'], '/')
        self.assertEqual(top['pageviews'], 2000)

    def test_limit_param(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'limit': 2},
        )
        self.assertEqual(len(res.data['data']), 2)

    def test_date_range(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-10'},
        )
        data = res.data['data']
        top = data[0]
        self.assertEqual(top['pageviews'], 1000)  # only one day

    def test_shrunk_mode_returns_limited_data_without_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'limit': 10},
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('data', res.data)
        self.assertNotIn('meta', res.data)
        self.assertEqual(len(res.data['data']), 10)

    # Paginated mode 
    def test_paginated_first_page_returns_correct_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 0, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('meta', res.data)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)          # unique pages
        self.assertIsNone(meta['previous'])
        self.assertIsNotNone(meta['next'])

    def test_paginated_second_page_has_previous_link(self):
        # Request second page
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 50, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        meta = res.data['meta']
        self.assertIsNotNone(meta['previous'])
        # Some implementations omit `offset=0` because it's the default.
        self.assertTrue('offset=0' in meta['previous'] or 'offset=' not in meta['previous'])
        # Next should be None because total=60, offset=50, so only 10 remaining
        self.assertIsNone(meta['next'])

    def test_paginated_offset_beyond_total_returns_empty_and_no_next(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 200, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 0)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)
        self.assertIsNotNone(meta['previous'])  # can go back
        self.assertIsNone(meta['next'])

    def test_paginated_custom_limit(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 0, 'limit': 5},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 5)
        self.assertEqual(res.data['meta']['limit'], 5)

class TopReferrersViewTests(AnalyticsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('top-referrers', kwargs={'site_id': self.site.id})
        # Create referrer stats for 2 days, enough rows to exercise pagination.
        for day in [date(2026, 5, 10), date(2026, 5, 11)]:
            # Deterministic top referrer.
            self._create_referrer_stats(self.site, day, 'Google', 'organic', visitors=25, pageviews=50)
            # 59 additional unique (source, medium) pairs (total unique rows = 60).
            for i in range(59):
                self._create_referrer_stats(self.site, day, f'Source-{i}', 'ref', visitors=1, pageviews=1)

    def test_returns_top_referrers(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11'},
        )
        data = res.data['data']
        self.assertGreaterEqual(len(data), 2)
        top = data[0]
        self.assertEqual(top['source'], 'Google')
        self.assertEqual(top['pageviews'], 100)  # sum over 2 days

    def test_limit_and_date_range(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'limit': 1, 'start': '2026-05-11', 'end': '2026-05-11'},
        )
        data = res.data['data']
        self.assertEqual(len(data), 1)
        # Google: 50 pageviews on May 11
        self.assertEqual(data[0]['pageviews'], 50)

    def test_shrunk_mode_returns_limited_data_without_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'limit': 10},
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('data', res.data)
        self.assertNotIn('meta', res.data)
        self.assertEqual(len(res.data['data']), 10)

    # Paginated mode 
    def test_paginated_first_page_returns_correct_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 0, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('meta', res.data)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)          # unique pages
        self.assertIsNone(meta['previous'])
        self.assertIsNotNone(meta['next'])

    def test_paginated_second_page_has_previous_link(self):
        # Request second page
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 50, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        meta = res.data['meta']
        self.assertIsNotNone(meta['previous'])
        self.assertTrue('offset=0' in meta['previous'] or 'offset=' not in meta['previous'])
        # Next should be None because total=60, offset=50, so only 10 remaining
        self.assertIsNone(meta['next'])

    def test_paginated_offset_beyond_total_returns_empty_and_no_next(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 200, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 0)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)
        self.assertIsNotNone(meta['previous'])  # can go back
        self.assertIsNone(meta['next'])

    def test_paginated_custom_limit(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 0, 'limit': 5},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 5)
        self.assertEqual(res.data['meta']['limit'], 5)


class CountriesViewTests(AnalyticsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('countries', kwargs={'site_id': self.site.id})
        # Create country stats for 2 days, enough rows to exercise pagination.
        for day in [date(2026, 5, 10), date(2026, 5, 11)]:
            # Deterministic top country.
            self._create_country_stats(self.site, day, 'United States', visitors=40)
            # 59 additional unique countries (total unique rows = 60).
            for i in range(59):
                self._create_country_stats(self.site, day, f'Country-{i}', visitors=1)

    def test_returns_countries(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11'},
        )
        data = res.data['data']
        self.assertGreaterEqual(len(data), 2)
        top = data[0]
        self.assertEqual(top['country'], 'United States')
        self.assertEqual(top['visitors'], 80)  # sum

    def test_shrunk_mode_returns_limited_data_without_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'limit': 10},
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('data', res.data)
        self.assertNotIn('meta', res.data)
        self.assertEqual(len(res.data['data']), 10)

    # Paginated mode 
    def test_paginated_first_page_returns_correct_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 0, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('meta', res.data)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)          # unique pages
        self.assertIsNone(meta['previous'])
        self.assertIsNotNone(meta['next'])

    def test_paginated_second_page_has_previous_link(self):
        # Request second page
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 50, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        meta = res.data['meta']
        self.assertIsNotNone(meta['previous'])
        self.assertTrue('offset=0' in meta['previous'] or 'offset=' not in meta['previous'])
        # Next should be None because total=60, offset=50, so only 10 remaining
        self.assertIsNone(meta['next'])

    def test_paginated_offset_beyond_total_returns_empty_and_no_next(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 200, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 0)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)
        self.assertIsNotNone(meta['previous'])  # can go back
        self.assertIsNone(meta['next'])

    def test_paginated_custom_limit(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 0, 'limit': 5},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 5)
        self.assertEqual(res.data['meta']['limit'], 5)


class DevicesViewTests(AnalyticsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('devices', kwargs={'site_id': self.site.id})
        for day in [date(2026, 5, 10), date(2026, 5, 11)]:
            # Deterministic top device type.
            self._create_device_stats(self.site, day, 'desktop', visitors=60)
            # 59 additional unique device types (total unique rows = 60).
            for i in range(59):
                self._create_device_stats(self.site, day, f'device-{i}', visitors=1)

    def test_returns_devices(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11'},
        )
        data = res.data['data']
        top = data[0]
        self.assertEqual(top['device_type'], 'desktop')
        self.assertEqual(top['visitors'], 120)

    def test_shrunk_mode_returns_limited_data_without_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'limit': 10},
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('data', res.data)
        self.assertNotIn('meta', res.data)
        self.assertEqual(len(res.data['data']), 10)

    # Paginated mode 
    def test_paginated_first_page_returns_correct_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 0, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('meta', res.data)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)          # unique pages
        self.assertIsNone(meta['previous'])
        self.assertIsNotNone(meta['next'])

    def test_paginated_second_page_has_previous_link(self):
        # Request second page
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 50, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        meta = res.data['meta']
        self.assertIsNotNone(meta['previous'])
        self.assertTrue('offset=0' in meta['previous'] or 'offset=' not in meta['previous'])
        # Next should be None because total=60, offset=50, so only 10 remaining
        self.assertIsNone(meta['next'])

    def test_paginated_offset_beyond_total_returns_empty_and_no_next(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 200, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 0)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)
        self.assertIsNotNone(meta['previous'])  # can go back
        self.assertIsNone(meta['next'])

    def test_paginated_custom_limit(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 0, 'limit': 5},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 5)
        self.assertEqual(res.data['meta']['limit'], 5)


class BrowsersViewTests(AnalyticsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('browsers', kwargs={'site_id': self.site.id})
        for day in [date(2026, 5, 10), date(2026, 5, 11)]:
            # Deterministic top browser.
            self._create_browser_stats(self.site, day, 'Chrome', visitors=70)
            # 59 additional unique browsers (total unique rows = 60).
            for i in range(59):
                self._create_browser_stats(self.site, day, f'Browser-{i}', visitors=1)

    def test_returns_browsers(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11'},
        )
        data = res.data['data']
        top = data[0]
        self.assertEqual(top['browser'], 'Chrome')
        self.assertEqual(top['visitors'], 140)

    def test_shrunk_mode_returns_limited_data_without_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'limit': 10},
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('data', res.data)
        self.assertNotIn('meta', res.data)
        self.assertEqual(len(res.data['data']), 10)

    # Paginated mode 
    def test_paginated_first_page_returns_correct_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 0, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('meta', res.data)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)          # unique pages
        self.assertIsNone(meta['previous'])
        self.assertIsNotNone(meta['next'])

    def test_paginated_second_page_has_previous_link(self):
        # Request second page
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 50, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        meta = res.data['meta']
        self.assertIsNotNone(meta['previous'])
        self.assertTrue('offset=0' in meta['previous'] or 'offset=' not in meta['previous'])
        # Next should be None because total=60, offset=50, so only 10 remaining
        self.assertIsNone(meta['next'])

    def test_paginated_offset_beyond_total_returns_empty_and_no_next(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 200, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 0)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)
        self.assertIsNotNone(meta['previous'])  # can go back
        self.assertIsNone(meta['next'])

    def test_paginated_custom_limit(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 0, 'limit': 5},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 5)
        self.assertEqual(res.data['meta']['limit'], 5)


class OSViewTests(AnalyticsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('os', kwargs={'site_id': self.site.id})
        for day in [date(2026, 5, 10), date(2026, 5, 11)]:
            # Deterministic top OS.
            self._create_os_stats(self.site, day, 'Windows', visitors=80)
            # 59 additional unique OS values (total unique rows = 60).
            for i in range(59):
                self._create_os_stats(self.site, day, f'OS-{i}', visitors=1)

    def test_returns_os(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11'},
        )
        data = res.data['data']
        top = data[0]
        self.assertEqual(top['os'], 'Windows')
        self.assertEqual(top['visitors'], 160)

    def test_shrunk_mode_returns_limited_data_without_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'limit': 10},
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('data', res.data)
        self.assertNotIn('meta', res.data)
        self.assertEqual(len(res.data['data']), 10)

    # Paginated mode 
    def test_paginated_first_page_returns_correct_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 0, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('meta', res.data)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)          # unique pages
        self.assertIsNone(meta['previous'])
        self.assertIsNotNone(meta['next'])

    def test_paginated_second_page_has_previous_link(self):
        # Request second page
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 50, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        meta = res.data['meta']
        self.assertIsNotNone(meta['previous'])
        self.assertTrue('offset=0' in meta['previous'] or 'offset=' not in meta['previous'])
        # Next should be None because total=60, offset=50, so only 10 remaining
        self.assertIsNone(meta['next'])

    def test_paginated_offset_beyond_total_returns_empty_and_no_next(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 200, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 0)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)
        self.assertIsNotNone(meta['previous'])  # can go back
        self.assertIsNone(meta['next'])

    def test_paginated_custom_limit(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-10', 'end': '2026-05-11', 'offset': 0, 'limit': 5},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 5)
        self.assertEqual(res.data['meta']['limit'], 5)


class TopRegionsViewTests(AnalyticsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('top-regions', kwargs={'site_id': self.site.id})
        # Create raw events for a date range, with region values
        test_date = date(2026, 5, 14)
        # Make "California" deterministically the top region.
        self._make_raw_events(
            self.site,
            test_date,
            visitor_ids=[f'ca{i}' for i in range(10)],
            urls=['/'],
            region='California',
            country='US',
        )
        # 59 additional unique regions (total unique regions = 60).
        for i in range(59):
            self._make_raw_events(
                self.site,
                test_date,
                visitor_ids=[f'r{i}'],
                urls=['/'],
                region=f'Region-{i}',
                country='US',
            )
        # Add some events with empty region to ensure they are excluded
        self._create_event(
            site=self.site,
            timestamp=django_timezone.make_aware(datetime(2026, 5, 14, 12, 0), timezone.utc),
            visitor_id='v9',
            url='/',
            region='',
            country='US',
        )

    def test_returns_top_regions(self):
        res = self.auth_client.get(self.url, {'interval': 'day', 'day': '2026-05-14'})
        data = res.data['data']
        self.assertGreaterEqual(len(data), 2)
        # First region should be California with most distinct visitors
        top = data[0]
        self.assertEqual(top['region'], 'California')
        self.assertEqual(top['visitors'], 10)

    def test_empty_regions_excluded(self):
        res = self.auth_client.get(self.url, {'interval': 'day', 'day': '2026-05-14'})
        data = res.data['data']
        regions = [r['region'] for r in data]
        self.assertNotIn('', regions)

    def test_date_range(self):
        # Only date 2026-05-14 has data, earlier dates return empty
        res = self.auth_client.get(
            self.url,
            {'interval': 'custom', 'start': '2026-05-13', 'end': '2026-05-13'},
        )
        self.assertEqual(len(res.data['data']), 0)

    def test_shrunk_mode_returns_limited_data_without_meta(self):
        res = self.auth_client.get(
            self.url, {'interval': 'day', 'day': '2026-05-14', 'limit': 10}
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('data', res.data)
        self.assertNotIn('meta', res.data)
        self.assertEqual(len(res.data['data']), 10)

    # Paginated mode 
    def test_paginated_first_page_returns_correct_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'day', 'day': '2026-05-14', 'offset': 0, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('meta', res.data)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)          # unique pages
        self.assertIsNone(meta['previous'])
        self.assertIsNotNone(meta['next'])

    def test_paginated_second_page_has_previous_link(self):
        # Request second page
        res = self.auth_client.get(
            self.url,
            {'interval': 'day', 'day': '2026-05-14', 'offset': 50, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        meta = res.data['meta']
        self.assertIsNotNone(meta['previous'])
        self.assertTrue('offset=0' in meta['previous'] or 'offset=' not in meta['previous'])
        # Next should be None because total=60, offset=50, so only 10 remaining
        self.assertIsNone(meta['next'])

    def test_paginated_offset_beyond_total_returns_empty_and_no_next(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'day', 'day': '2026-05-14', 'offset': 200, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 0)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)
        self.assertIsNotNone(meta['previous'])  # can go back
        self.assertIsNone(meta['next'])

    def test_paginated_custom_limit(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'day', 'day': '2026-05-14', 'offset': 0, 'limit': 5},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 5)
        self.assertEqual(res.data['meta']['limit'], 5)


class TopCitiesViewTests(AnalyticsTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('top-cities', kwargs={'site_id': self.site.id})
        test_date = date(2026, 5, 14)
        # Make "Los Angeles" deterministically the top city.
        self._make_raw_events(
            self.site,
            test_date,
            visitor_ids=[f'la{i}' for i in range(10)],
            urls=['/'],
            city='Los Angeles',
            country='US',
        )
        # 59 additional unique cities (total unique cities = 60).
        for i in range(59):
            self._make_raw_events(
                self.site,
                test_date,
                visitor_ids=[f'c{i}'],
                urls=['/'],
                city=f'City-{i}',
                country='US',
            )

    def test_returns_top_cities(self):
        res = self.auth_client.get(self.url, {'interval': 'day', 'day': '2026-05-14'})
        data = res.data['data']
        self.assertGreaterEqual(len(data), 2)
        top = data[0]
        self.assertEqual(top['city'], 'Los Angeles')
        self.assertEqual(top['visitors'], 10)

    def test_empty_cities_excluded(self):
        # create event with no city
        self._create_event(
            site=self.site,
            timestamp=django_timezone.make_aware(datetime(2026, 5, 14, 12, 0), timezone.utc),
            visitor_id='c1',
            url='/',
            city='',
        )
        res = self.auth_client.get(self.url, {'interval': 'day', 'day': '2026-05-14'})
        data = res.data['data']
        cities = [c['city'] for c in data]
        self.assertNotIn('', cities)

    def test_shrunk_mode_returns_limited_data_without_meta(self):
        res = self.auth_client.get(
            self.url, {'interval': 'day', 'day': '2026-05-14', 'limit': 10}
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('data', res.data)
        self.assertNotIn('meta', res.data)
        self.assertEqual(len(res.data['data']), 10)

    # Paginated mode 
    def test_paginated_first_page_returns_correct_meta(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'day', 'day': '2026-05-14', 'offset': 0, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('meta', res.data)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)          # unique pages
        self.assertIsNone(meta['previous'])
        self.assertIsNotNone(meta['next'])

    def test_paginated_second_page_has_previous_link(self):
        # Request second page
        res = self.auth_client.get(
            self.url,
            {'interval': 'day', 'day': '2026-05-14', 'offset': 50, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        meta = res.data['meta']
        self.assertIsNotNone(meta['previous'])
        self.assertTrue('offset=0' in meta['previous'] or 'offset=' not in meta['previous'])
        # Next should be None because total=60, offset=50, so only 10 remaining
        self.assertIsNone(meta['next'])

    def test_paginated_offset_beyond_total_returns_empty_and_no_next(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'day', 'day': '2026-05-14', 'offset': 200, 'limit': 50}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 0)
        meta = res.data['meta']
        self.assertEqual(meta['total'], 60)
        self.assertIsNotNone(meta['previous'])  # can go back
        self.assertIsNone(meta['next'])

    def test_paginated_custom_limit(self):
        res = self.auth_client.get(
            self.url,
            {'interval': 'day', 'day': '2026-05-14', 'offset': 0, 'limit': 5},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['data']), 5)
        self.assertEqual(res.data['meta']['limit'], 5)
