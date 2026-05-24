import random
import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from sites.models import Site
from tracking.models import Event
from analytics.services import AggregationService

User = get_user_model()

BROWSERS = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera']
OS_LIST = ['Windows', 'macOS', 'Linux', 'Android', 'iOS']
DEVICES = ['desktop', 'mobile', 'tablet']
COUNTRIES = ['United States', 'Germany', 'Japan', 'Brazil', 'India', 'United Kingdom']
REGIONS = ['California', 'Bavaria', 'Tokyo', 'São Paulo', 'Maharashtra', 'England']
CITIES = ['Los Angeles', 'Munich', 'Tokyo', 'São Paulo', 'Mumbai', 'London']
REFERRERS = [
    ('https://www.google.com/', 'Google', 'organic'),
    ('https://www.facebook.com/', 'Facebook', 'social'),
    ('https://twitter.com/', 'Twitter', 'social'),
    ('https://www.bing.com/', 'Bing', 'organic'),
    ('https://duckduckgo.com/', 'DuckDuckGo', 'organic'),
    ('', 'Direct', 'none'),
]

class Command(BaseCommand):
    help = 'Seed dummy data for load testing (1000 users, sites, events)'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing analytics data before seeding')
        parser.add_argument('--users', type=int, default=1000, help='Number of users')
        parser.add_argument('--events-per-site', type=int, default=100, help='Events per site')

    def handle(self, *args, **options):
        clear = options['clear']
        num_users = options['users']
        events_per_site = options['events_per_site']

        if clear:
            self.stdout.write('Clearing existing analytics data...')
            Event.objects.all().delete()
            # Delete all analytics aggregated tables 
            from analytics.models import (
                DailySiteStats, DailyPageStats, DailyReferrerStats,
                DailyCountryStats, DailyDeviceStats, DailyBrowserStats, DailyOSStats
            )
            for model in [DailySiteStats, DailyPageStats, DailyReferrerStats,
                          DailyCountryStats, DailyDeviceStats, DailyBrowserStats, DailyOSStats]:
                model.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Old data cleared.'))

        # --- 1. Create dummy users ---
        self.stdout.write(f'Creating {num_users} users...')
        with transaction.atomic():
            users = []
            
            for i in range(num_users):
                users.append(User(
                    email=f'loadtest{i:04d}@example.com',
                    name=f'Load Test {i}',
                    is_active=True,
                    is_staff=False,
                    is_suspended=False,
                ))
            User.objects.bulk_create(users, batch_size=500)
            # Re-fetch users with IDs (bulk_create doesn't return IDs on some DBs)
            users = list(User.objects.filter(email__startswith='loadtest'))

            # --- 2. Create sites ---
            self.stdout.write('Creating sites...')
            sites_list = []
            for user in users:
                tracking_token = uuid.uuid4().hex
                domain = f'loadtest-{random.randint(0, 99999)}.example.com'
                sites_list.append(Site(
                    user=user,
                    domain=domain,
                    tracking_token=tracking_token,
                    timezone=random.choice(['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo']),
                    ))
            Site.objects.bulk_create(sites_list, batch_size=500)
            sites = list(Site.objects.filter(domain__startswith='loadtest-'))

            # --- 3. Create raw events for each site ---
            self.stdout.write(f'Creating {events_per_site} events per site ({len(sites)} sites)...')
            now = timezone.now()
            event_batch = []
            for site in sites:
                for _ in range(events_per_site):
                    # Random timestamp in last 30 days
                    days_ago = random.randint(0, 30)
                    seconds_offset = random.randint(0, 86400 - 1)
                    ts = now - timedelta(days=days_ago, seconds=seconds_offset)

                    ref = random.choice(REFERRERS)
                    visitor = str(uuid.uuid4())
                    page = random.choice(['/', '/about', '/contact', '/products', '/blog/post'])
                    country = random.choice(COUNTRIES)
                    region = random.choice(REGIONS)
                    city = random.choice(CITIES)

                    event_batch.append(Event(
                        site=site,
                        timestamp=ts,
                        visitor_id=visitor,
                        url=f'https://{site.domain}{page}',
                        referrer=ref[0],
                        source=ref[1],
                        medium=ref[2],
                        browser=random.choice(BROWSERS),
                        os=random.choice(OS_LIST),
                        device_type=random.choice(DEVICES),
                        country=country,
                        region=region,
                        city=city,
                        ip_address='127.0.0.1',
                        user_agent='Mozilla/5.0 ...',
                        timezone='UTC',
                    ))

                    # Bulk insert every 1000 events to avoid memory issues
                    if len(event_batch) >= 1000:
                        Event.objects.bulk_create(event_batch, batch_size=1000)
                        self.stdout.write(f'{len(event_batch)} events created')
                        event_batch = []
            # Insert remaining
            if event_batch:
                Event.objects.bulk_create(event_batch, batch_size=1000)
                self.stdout.write(f'{len(event_batch)} remaining events created')
            
            self.stdout.write(self.style.SUCCESS('All Events created.'))

            # --- 4. Run aggregation for all affected sites ---
            self.stdout.write('Running daily aggregation (this may take a moment)...')
            # Aggregate each site's events for the last 30 days
            for site in sites:
                # Find the distinct dates for this site's events
                dates = Event.objects.filter(site=site).dates('timestamp', 'day')
                for d in dates:
                    AggregationService().aggregate_date(site, d)

            self.stdout.write(self.style.SUCCESS('Aggregation complete. Dummy data ready.'))