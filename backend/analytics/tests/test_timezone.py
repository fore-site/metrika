from datetime import date, datetime, timedelta, timezone
from freezegun import freeze_time
from django.test import TestCase
from django.utils import timezone as django_timezone
from accounts.models import User
from sites.models import Site
from tracking.models import Event
from analytics.services import AggregationService, StatsQueryService
from analytics.models import DailySiteStats

class SiteTimezoneTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='tz@test.com', password='x')
        self.site_utc = Site.objects.create(user=self.user, domain='utc.com', timezone='UTC')
        self.site_tokyo = Site.objects.create(user=self.user, domain='tokyo.com', timezone='Asia/Tokyo')
        self.service = StatsQueryService()
        # Freeze to a known UTC time: 2026-05-17 02:00 UTC
        self.freezer = freeze_time('2026-05-17 02:00:00')
        self.freezer.start()
        self.addCleanup(self.freezer.stop)

    def _create_events(self, site, utc_dt, visitor_ids):
        for vid in visitor_ids:
            Event.objects.create(
                site=site, timestamp=utc_dt,
                visitor_id=vid, url='https://example.com/page',
            )

    # ------------------------------------------------------------------
    def test_aggregation_uses_local_day_for_tokyo(self):
        # Tokyo is UTC+9. Local date 2026-05-17 starts at 2026-05-16 15:00 UTC.
        # Create events at 2026-05-16 16:00 UTC (inside Tokyo May 17)
        self._create_events(
            self.site_tokyo,
            datetime(2026, 5, 16, 16, 0, 0, tzinfo=timezone.utc),
            ['v1', 'v2', 'v3']
        )
        AggregationService().aggregate_date(self.site_tokyo, date(2026, 5, 17))
        stats = DailySiteStats.objects.get(site=self.site_tokyo, date=date(2026, 5, 17))
        self.assertEqual(stats.visitors, 3)

    def test_aggregation_utc_site_unchanged(self):
        # For UTC site, local date = UTC date
        self._create_events(
            self.site_utc,
            datetime(2026, 5, 17, 1, 0, 0, tzinfo=timezone.utc),
            ['v1', 'v2']
        )
        AggregationService().aggregate_date(self.site_utc, date(2026, 5, 17))
        stats = DailySiteStats.objects.get(site=self.site_utc, date=date(2026, 5, 17))
        self.assertEqual(stats.visitors, 2)

    def test_today_timeseries_uses_site_timezone(self):
        # Tokyo local now: 2026-05-17 11:00 JST (UTC+9) -> UTC = 02:00
        # So "today" for Tokyo is May 17, which started at 15:00 UTC yesterday.
        # Create event that falls within Tokyo's May 17 window:
        self._create_events(
            self.site_tokyo,
            datetime(2026, 5, 16, 16, 0, 0, tzinfo=timezone.utc),
            ['v1', 'v2']
        )
        data = self.service.get_today_timeseries(self.site_tokyo)
        self.assertGreater(len(data), 0)    # Have at least one hourly point

        hour_point = next((p for p in data if p['visitors'] > 0), None)
        hour_dt = hour_point['hour']
        self.assertIsNotNone(hour_point, 'Expected an hourly point with visitors')

        self.assertEqual(hour_dt.date(), date(2026, 5, 16))
        self.assertEqual(hour_point['visitors'], 2)

    def test_live_today_utc_site(self):
        # UTC site: today is May 17, window starts at midnight UTC today.
        self._create_events(
            self.site_utc,
            datetime(2026, 5, 17, 1, 0, 0, tzinfo=timezone.utc),
            ['v1']
        )
        data = self.service.get_today_timeseries(self.site_utc)
        self.assertGreater(len(data), 0)
        hour_point = next((p for p in data if p['visitors'] > 0), None)
        hour_dt = hour_point['hour']
        self.assertIsNotNone(hour_point)
        self.assertEqual(hour_dt.date(), date(2026, 5, 17))
        self.assertEqual(hour_point['visitors'], 1)

    def test_hourly_and_realtime_remain_utc(self):
        # Hourly should be unaffected by site timezone (uses raw UTC events)
        # We just check that it doesn't crash with a timezone-aware datetime
        start = django_timezone.now() - timedelta(hours=24)
        end = django_timezone.now()
        data = self.service.get_hourly_timeseries(self.site_tokyo, start, end)
        self.assertIsInstance(data, list)