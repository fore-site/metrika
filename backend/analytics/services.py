from datetime import date, timedelta, datetime
from django.db import transaction
from django.db.models import Sum, Count
from .models import (
    DailySiteStats,
    DailyPageStats,
    DailyReferrerStats,
    DailyCountryStats,
    DailyDeviceStats,
    DailyBrowserStats,
    DailyOSStats,
)
from tracking.services import EventService
from django.utils import timezone
from collections import defaultdict
from decimal import Decimal
from django.db.models.functions import TruncHour


class AggregationService:
    """Populate daily summary tables for a given site and date."""

    def get_session_metrics(self, site_id, day: date | None = None, 
                            start_date: date | None = None, 
                            end_date: date | None = None):
        """
        Returns dict with:
          - total_sessions
          - bounce_rate (0-100)
          - avg_duration_seconds
          - views_per_visit
        """
        # 1. Fetch all events for the day, ordered by visitor and time
        if day:
            events = (EventService().get_site_events(site_id, day)
                .order_by('visitor_id', 'timestamp')
                .values('visitor_id', 'timestamp')
            )
        else:
            if start_date and end_date:
                events = (EventService().get_site_events_date_range(site_id, start_date, end_date)
                        .order_by('visitor_id', 'timestamp')
                        .values('visitor_id', 'timestamp')
                        )
            else:
                raise Exception('Must pass in either day or start and end date.')

        # 2. Group events by visitor_id
        visitor_events = defaultdict(list)
        for e in events:
            visitor_events[e['visitor_id']].append(e['timestamp'])

        # 3. Split into sessions (30-minute timeout)
        SESSION_TIMEOUT = timedelta(minutes=30)
        total_sessions = 0
        single_page_sessions = 0
        total_duration = timedelta(0)   # for average duration
        total_pageviews_in_sessions = 0

        for visitor_id, timestamps in visitor_events.items():
            # timestamps are already sorted (thanks to ORM ordering)
            session_start = None
            session_end = None
            pages_in_session = 0

            for ts in timestamps:
                if session_start is None:
                    # Start a new session
                    session_start = ts
                    session_end = ts
                    pages_in_session = 1
                    total_sessions += 1
                elif (ts - session_end) > SESSION_TIMEOUT:
                    # End previous session and start new one
                    # First, record the old session
                    total_pageviews_in_sessions += pages_in_session
                    if pages_in_session == 1:
                        single_page_sessions += 1
                    total_duration += (session_end - session_start)

                    # Start new session
                    session_start = ts
                    session_end = ts
                    pages_in_session = 1
                    total_sessions += 1
                else:
                    # Extend current session
                    session_end = ts
                    pages_in_session += 1

            # The last session of this visitor
            if session_start:
                total_pageviews_in_sessions += pages_in_session
                if pages_in_session == 1:
                    single_page_sessions += 1
                total_duration += (session_end - session_start)

        # 4. Calculate metrics
        bounce_rate = (single_page_sessions / total_sessions * 100) if total_sessions else 0
        avg_duration_seconds = (
            total_duration.total_seconds() / total_sessions
        ) if total_sessions else 0
        views_per_visit = (
            total_pageviews_in_sessions / total_sessions
        ) if total_sessions else 0

        return {
            'total_visits': total_sessions,
            'bounce_rate': round(bounce_rate),
            'avg_visit_duration': round(avg_duration_seconds),
            'views_per_visit': str(round(views_per_visit, 2)),
        }

    def aggregate_date(self, site_id: int, day: date):
        events = EventService().get_site_events(site_id, day)
        session_metrics = self.get_session_metrics(site_id, day)
        if not events.exists():
            return

        with transaction.atomic():
            # Site totals
            site_data = events.aggregate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            DailySiteStats.objects.update_or_create(
                site_id=site_id,
                date=day,
                defaults={
                    'visitors': site_data['visitors'],
                    'pageviews': site_data['pageviews'],
                    'total_visits': session_metrics.get('total_visits'),
                    'bounce_rate': session_metrics.get('bounce_rate'),
                    'avg_visit_duration': session_metrics.get('avg_visit_duration'),
                    'views_per_visit': Decimal(str(session_metrics.get('views_per_visit')))
                }
            )

            # Page stats
            page_data = events.values('url').annotate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            for row in page_data:
                DailyPageStats.objects.update_or_create(
                    site_id=site_id,
                    date=day,
                    path=row['url'],
                    defaults={
                        'visitors': row['visitors'],
                        'pageviews': row['pageviews'],
                    }
                )

            # Referrer stats
            referrer_data = events.values('source', 'medium').annotate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            for row in referrer_data:
                DailyReferrerStats.objects.update_or_create(
                    site_id=site_id,
                    date=day,
                    source=row['source'] or 'Direct',
                    medium=row['medium'] or 'none',
                    defaults={
                        'visitors': row['visitors'],
                        'pageviews': row['pageviews'],
                    }
                )

            # Country stats
            country_data = events.values('country').annotate(
                visitors=Count('visitor_id', distinct=True),
            )
            for row in country_data:
                if row['country']:
                    DailyCountryStats.objects.update_or_create(
                        site_id=site_id,
                        date=day,
                        country=row['country'],
                        defaults={'visitors': row['visitors']}
                    )

            # Device stats
            device_data = events.values('device_type').annotate(
                visitors=Count('visitor_id', distinct=True),
            )
            for row in device_data:
                if row['device_type']:
                    DailyDeviceStats.objects.update_or_create(
                        site_id=site_id,
                        date=day,
                        device_type=row['device_type'],
                        defaults={'visitors': row['visitors']}
                    )

            # Browser stats
            browser_data = events.values('browser').annotate(
                visitors=Count('visitor_id', distinct=True),
            )
            for row in browser_data:
                if row['browser']:
                    DailyBrowserStats.objects.update_or_create(
                        site_id=site_id,
                        date=day,
                        browser=row['browser'],
                        defaults={'visitors': row['visitors']}
                    )

            # OS stats
            os_data = events.values('os').annotate(
                visitors=Count('visitor_id', distinct=True),
            )
            for row in os_data:
                if row['os']:
                    DailyOSStats.objects.update_or_create(
                        site_id=site_id,
                        date=day,
                        os=row['os'],
                        defaults={'visitors': row['visitors']}
                    )

class StatsQueryService:
    """Read operations for the dashboard."""

    def get_site_summary(self, site_id: int, start_date: date, end_date: date):
        stats = DailySiteStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(
            visitors=Sum('visitors'),
            pageviews=Sum('pageviews'),
        )
        session_metrics = AggregationService().get_session_metrics(site_id, start_date=start_date, end_date=end_date)
        stats.update(session_metrics)
        return stats

    def get_timeseries(self, site_id: int, start_date: date, end_date: date):
        stats = DailySiteStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        ).order_by('date').values('date', 'visitors', 'pageviews', 
                                  'total_visits', 'bounce_rate', 'avg_visit_duration',
                                  'views_per_visit')

        return stats

    def get_top_pages(self, site_id: int, start_date: date, end_date: date, limit: int =10):
        return DailyPageStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        ).values('path').annotate(
            visitors=Sum('visitors'),
            pageviews=Sum('pageviews'),
        ).order_by('-pageviews')[:limit]

    def get_top_referrers(self, site_id: int, start_date: date, end_date: date, limit: int =10):
        return DailyReferrerStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        ).values('source', 'medium').annotate(
            visitors=Sum('visitors'),
            pageviews=Sum('pageviews'),
        ).order_by('-pageviews')[:limit]

    def get_country_breakdown(self, site_id: int, start_date: date, end_date: date):
        return DailyCountryStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        ).values('country').annotate(visitors=Sum('visitors')).order_by('-visitors')

    def get_device_breakdown(self, site_id: int, start_date: date, end_date: date):
        return DailyDeviceStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        ).values('device_type').annotate(visitors=Sum('visitors')).order_by('-visitors')

    def get_browser_breakdown(self, site_id: int, start_date: date, end_date: date):
        return DailyBrowserStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        ).values('browser').annotate(visitors=Sum('visitors')).order_by('-visitors')

    def get_os_breakdown(self, site_id: int, start_date: date, end_date: date):
        return DailyOSStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        ).values('os').annotate(visitors=Sum('visitors')).order_by('-visitors')
    
    def get_top_regions(self, site_id, start: date, end: date, limit: int = 10):
        event = EventService().get_site_events_date_range(site_id, start, end)
        
        top_regions = event.values('region').annotate(
            visitors=Count('visitor_id', distinct=True),
        ).order_by('-visitors')[:limit]
        return top_regions

    def get_top_cities(self, site_id, start: date, end: date, limit: int = 10):
        event = EventService().get_site_events_date_range(site_id, start, end)
        
        top_cities = event.values('city').annotate(
            visitors=Count('visitor_id', distinct=True),
        ).order_by('-visitors')[:limit]
        return top_cities
    
    # Helpers for any specific day except current (incomplete) day
    def get_anyday_site_summary(self, site_id: int, day: date):
        stats = DailySiteStats.objects.filter(
            site_id=site_id,
            date=day
        ).aggregate(
            visitors=Sum('visitors'),
            pageviews=Sum('pageviews'),
        )
        return stats

    def get_anyday_timeseries(self, site_id: int, day: date):
        return DailySiteStats.objects.filter(
            site_id=site_id,
            date=day
        ).order_by('date').values('date', 'visitors', 'pageviews', 
                                  'total_visits', 'bounce_rate', 'avg_visit_duration',
                                  'views_per_visit')

    def get_anyday_top_pages(self, site_id: int, day: date, limit: int =10):
        return DailyPageStats.objects.filter(
            site_id=site_id,
            date=day
        ).values('path').annotate(
            visitors=Sum('visitors'),
            pageviews=Sum('pageviews'),
        ).order_by('-pageviews')[:limit]

    def get_anyday_top_referrers(self, site_id: int, day: date, limit: int =10):
        return DailyReferrerStats.objects.filter(
            site_id=site_id,
            date=day,
        ).values('source', 'medium').annotate(
            visitors=Sum('visitors'),
            pageviews=Sum('pageviews'),
        ).order_by('-pageviews')[:limit]

    def get_anyday_country_breakdown(self, site_id: int, day: date):
        return DailyCountryStats.objects.filter(
            site_id=site_id,
            date=day,
        ).values('country').annotate(visitors=Sum('visitors')).order_by('-visitors')

    def get_anyday_device_breakdown(self, site_id: int, day: date):
        return DailyDeviceStats.objects.filter(
            site_id=site_id,
            date=day,
        ).values('device_type').annotate(visitors=Sum('visitors')).order_by('-visitors')

    def get_anyday_browser_breakdown(self, site_id: int, day: date):
        return DailyBrowserStats.objects.filter(
            site_id=site_id,
            date=day,
        ).values('browser').annotate(visitors=Sum('visitors')).order_by('-visitors')

    def get_anyday_os_breakdown(self, site_id: int, day: date):
        return DailyOSStats.objects.filter(
            site_id=site_id,
            date=day,
        ).values('os').annotate(visitors=Sum('visitors')).order_by('-visitors')
    
    def get_anyday_top_regions(self, site_id, day: date, limit: int = 10):
        event = EventService().get_site_events(site_id, day)
        
        top_regions = event.values('region').annotate(
            visitors=Count('visitor_id', distinct=True),
        ).order_by('-visitors')[:limit]
        return top_regions

    def get_anyday_top_cities(self, site_id, day: date, limit: int = 10):
        event = EventService().get_site_events(site_id, day)
        
        top_cities = event.values('city').annotate(
            visitors=Count('visitor_id', distinct=True),
        ).order_by('-visitors')[:limit]
        return top_cities


    # Raw‑event helpers for the current (incomplete) day
    def get_today_site_summary(self, site_id):
        today = timezone.now().date()
        stats = EventService().get_site_events(site_id, today).aggregate(
            visitors=Count('visitor_id', distinct=True),
            pageviews=Count('id'),
        )
        session_metrics = AggregationService().get_session_metrics(site_id, day=today)
        stats.update(session_metrics)
        return stats

    def get_today_timeseries(self, site_id: int):
        """Return one data point for today from raw events."""
        today = date.today()
        data = (EventService().get_site_events(site_id, today)
                .order_by('date').values('date', 'visitors', 'pageviews', 
                                  'total_visits', 'bounce_rate', 'avg_visit_duration',
                                  'views_per_visit'))
        
        return data

    def get_today_top_pages(self, site_id: int, limit: int = 10):
        today = date.today()
        return (
            EventService().get_site_events(site_id, today)
            .values('url')
            .annotate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            .order_by('-pageviews')[:limit]
        )

    def get_today_top_referrers(self, site_id: int, limit: int = 10):
        today = date.today()
        return (
            EventService().get_site_events(site_id, today)
            .values('source', 'medium')
            .annotate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            .order_by('-pageviews')[:limit]
        )

    def get_today_country_breakdown(self, site_id: int):
        today = date.today()
        return (
            EventService().get_site_events(site_id, today)
            .values('country')
            .annotate(visitors=Count('visitor_id', distinct=True))
            .order_by('-visitors')
        )

    def get_today_device_breakdown(self, site_id: int):
        today = date.today()
        return (EventService().get_site_events(site_id, today)
                .values('device_type')
                .annotate(visitors=Sum('visitors'))
                .order_by('-visitors'))

    def get_today_browser_breakdown(self, site_id: int):
        today = date.today()
        return (EventService().get_site_events(site_id, today)
                .values('browser')
                .annotate(visitors=Sum('visitors'))
                .order_by('-visitors'))

    def get_today_os_breakdown(self, site_id: int):
        today = date.today()
        return (EventService().get_site_events(site_id, today)
                .values('os')
                .annotate(visitors=Sum('visitors'))
                .order_by('-visitors'))
    
    def get_today_top_regions(self, site_id, limit: int = 10):
        today = date.today()
        event = EventService().get_site_events(site_id, today)
        
        top_regions = event.values('region').annotate(
            visitors=Count('visitor_id', distinct=True),
        ).order_by('-visitors')[:limit]
        return top_regions


    def get_today_top_cities(self, site_id, limit: int = 10):
        today = date.today()
        event = EventService().get_site_events(site_id, today)
        
        top_cities = event.values('city').annotate(
            visitors=Count('visitor_id', distinct=True),
        ).order_by('-visitors')[:limit]
        return top_cities


    def get_hourly_timeseries(self, site_id: int, start_dt: datetime, end_dt: datetime):
        """
        Return one row per hour with visitors and pageviews.
        start_dt / end_dt are timezone‑aware datetimes (UTC).
        """
        return (EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
            .annotate(hour=TruncHour('timestamp'))
            .values('hour')
            .annotate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            .order_by('hour')
        )

    def get_realtime_stats(self, site_id: int, minutes: int = 5):
        """
        Return visitors and pageviews in the last `minutes` minutes.
        """
        since = timezone.now() - timedelta(minutes=minutes)
        data = EventService().get_site_events_realtime(site_id, since).aggregate(
            visitors=Count('visitor_id', distinct=True),
            pageviews=Count('id'),
        )
        return {
            'visitors': data['visitors'] or 0,
            'pageviews': data['pageviews'] or 0,
            'last_updated': timezone.now().isoformat(),
        }