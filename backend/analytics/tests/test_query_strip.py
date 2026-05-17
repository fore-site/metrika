from datetime import date, datetime, timezone, timedelta
from django.test import TestCase
from accounts.models import User
from sites.models import Site
from tracking.models import Event
from analytics.services import AggregationService
from analytics.models import DailyPageStats

class QueryStrippingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='a@b.com', password='x')
        self.site = Site.objects.create(user=self.user, domain='example.com')
        self.today = date(2026, 5, 17)
        # Create raw events with query strings
        base_time = datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc)
        Event.objects.create(
            site=self.site,
            timestamp=base_time,
            visitor_id='v1',
            url='https://example.com/page?a=1',
        )
        Event.objects.create(
            site=self.site,
            timestamp=base_time + timedelta(minutes=1),
            visitor_id='v2',
            url='https://example.com/page?b=2',
        )
        Event.objects.create(
            site=self.site,
            timestamp=base_time + timedelta(minutes=2),
            visitor_id='v3',
            url='https://example.com/other',
        )

    def test_aggregation_strips_query_strings(self):
        AggregationService().aggregate_date(self.site, self.today)
        pages = DailyPageStats.objects.filter(site=self.site, date=self.today)
        # Should have two paths: '/page' and '/other'
        self.assertEqual(pages.count(), 2)
        page_row = pages.get(url__endswith='/page')  # path stored without query
        self.assertEqual(page_row.pageviews, 2)
        self.assertEqual(page_row.visitors, 2)  # two distinct visitors