from datetime import date, timedelta, datetime
from django.db import transaction
from django.db.models import Sum, Count, BaseManager
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
from tracking.models import Event
from django.utils import timezone
from collections import defaultdict
from django.db.models.functions import TruncHour, TruncDate


class AggregationService:
    """Populate daily summary tables for a given site and date."""

    def get_session_metrics(self, site_id, day: date | None = None, 
                            start_date: date | None = None, 
                            end_date: date | None = None,
                            start_dt: datetime | None = None,
                            end_dt: datetime | None = None):
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
        elif start_dt and end_dt:
            events = (EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
                      .order_by('visitor_id', 'timestamp')
                      .values('visitor_id', 'timestamp'))
        else:
            if start_date and end_date:
                events = (EventService().get_site_events_date_range(site_id, start_date, end_date)
                        .order_by('visitor_id', 'timestamp')
                        .values('visitor_id', 'timestamp')
                        )
            else:
                raise Exception('Must pass in either day, start and end date or start and end datetime.')

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

        return {
            'total_visits': total_sessions,
            'single_page_sessions': single_page_sessions,
            'total_duration_seconds': total_duration.total_seconds(),
            'total_pageviews_in_sessions': total_pageviews_in_sessions,
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
                    'single_page_sessions': session_metrics.get('single_page_sessions'),
                    'total_duration_seconds': session_metrics.get('total_duration_seconds'),
                    'total_pageviews_in_sessions': session_metrics.get('total_pageviews_in_sessions')
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

    def _site_summary(self, stat: BaseManager[DailySiteStats]):
        summary = stat.aggregate(
            visitors=Sum('visitors'),
            pageviews=Sum('pageviews'),
            total_visits=Sum('total_visits'),
            total_pageviews_in_sessions=Sum('total_pageviews_in_sessions'),
            total_duration_seconds=Sum('total_duration_seconds'),
            single_page_sessions=Sum('single_page_sessions'),
        )
        sessions = summary['total_visits'] or 0
        summary['bounce_rate'] = round(summary['single_page_sessions'] / sessions * 100) if sessions else 0
        summary['avg_duration_seconds'] = round(summary['total_duration_seconds'] / sessions * 100) if sessions else 0
        summary['views_per_visit'] = round(summary['total_pageviews_in_sessions'] / sessions * 100, 2) if sessions else 0.00

        return summary

    def _timeseries(self, stat: BaseManager[DailySiteStats]):
        rows = stat.order_by('date').values('date', 'visitors', 'pageviews', 
                                  'total_visits', 'single_page_sessions', 'total_duration_seconds',
                                  'total_pageviews_in_sessions')
        timeseries = []
        for row in rows:
            sessions = row['total_visits'] or 0
            row['bounce_rate'] = round(row['single_page_sessions'] / sessions * 100) if sessions else 0
            row['avg_durations_seconds'] = round(row['total_duration_seconds'] / sessions * 100) if sessions else 0
            row['views_per_visit'] = round(row['total_pageviews_in_sessions'] / sessions * 100, 2) if sessions else 0.00

            timeseries.append(row)
        return timeseries
    
    def _top_pages(self, stat: BaseManager[DailyPageStats]):
        return stat.values('path').annotate(
            visitors=Sum('visitors'),
            pageviews=Sum('pageviews'),
        ).order_by('-pageviews')
    
    def _top_referrers(self, stat: BaseManager[DailyReferrerStats]):
        return stat.values('source', 'medium').annotate(
            visitors=Sum('visitors'),
            pageviews=Sum('pageviews'),
        ).order_by('-pageviews')
    
    def _country_breakdown(self, stat: BaseManager[DailyCountryStats]):
        return stat.values('country').annotate(visitors=Sum('visitors')).order_by('-visitors')
    
    def _device_breakdown(self, stat: BaseManager[DailyDeviceStats]):
        return stat.values('device_type').annotate(visitors=Sum('visitors')).order_by('-visitors')

    def _browser_breakdown(self, stat: BaseManager[DailyBrowserStats]):
        return stat.values('browser').annotate(visitors=Sum('visitors')).order_by('-visitors')

    def _os_breakdown(self, stat: BaseManager[DailyOSStats]):
        return stat.values('os').annotate(visitors=Sum('visitors')).order_by('-visitors')

    def _top_regions(self, event: BaseManager[Event]):
        return event.values('region').annotate(
            visitors=Count('visitor_id', distinct=True),
        ).order_by('-visitors')
    
    def _top_cities(self, event: BaseManager[Event]):
        return event.values('city').annotate(
            visitors=Count('visitor_id', distinct=True),
        ).order_by('-visitors')

    def get_site_summary(self, site_id: int, start_date: date, end_date: date):
        stats = DailySiteStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        )
        summary = self._site_summary(stats)
        return summary

    def get_timeseries(self, site_id: int, start_date: date, end_date: date):
        data = (EventService().get_site_events_date_range(site_id, start=start_date, end=end_date)
                .annotate(date=TruncDate('timestamp'))
                .values('date')
                .annotate(
                    visitors=Count('visitor_id', distinct=True),
                    pageviews=Count('id'),
                )
                .order_by('date')
        )
        timeseries = []
        for event in data:
            day = event['date'] 
            session_metrics = AggregationService().get_session_metrics(site_id, day=day)
            sessions = session_metrics['total_visits']
            event['bounce_rate'] = round(session_metrics['single_page_sessions'] / sessions * 100) if sessions else 0
            event['avg_durations_seconds'] = round(session_metrics['total_duration_seconds'] / sessions * 100) if sessions else 0
            event['views_per_visit'] = round(session_metrics['total_pageviews_in_sessions'] / sessions * 100, 2) if sessions else 0.00
            timeseries.append(event)
        return timeseries

    def get_top_pages(self, site_id: int, start_date: date, end_date: date, limit: int =10):
        stats = DailyPageStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        )
        top_pages = self._top_pages(stats)
        return top_pages[:limit]

    def get_top_referrers(self, site_id: int, start_date: date, end_date: date, limit: int =10):
        stats = DailyReferrerStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        )
        top_referrers = self._top_referrers(stats)
        return top_referrers[:limit]

    def get_country_breakdown(self, site_id: int, start_date: date, end_date: date):
        stats = DailyCountryStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        )
        country_breakdown = self._country_breakdown(stats)
        return country_breakdown

    def get_device_breakdown(self, site_id: int, start_date: date, end_date: date):
        stats = DailyDeviceStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        )
        device_breakdown = self._device_breakdown(stats)
        return device_breakdown


    def get_browser_breakdown(self, site_id: int, start_date: date, end_date: date):
        stats = DailyBrowserStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        )
        browser_breakdown = self._browser_breakdown(stats)
        return browser_breakdown

    def get_os_breakdown(self, site_id: int, start_date: date, end_date: date):
        stats = DailyOSStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        )
        os_breakdown = self._os_breakdown(stats)
        return os_breakdown
    
    
    def get_top_regions(self, site_id, start: date, end: date, limit: int = 10):
        event = EventService().get_site_events_date_range(site_id, start, end)
        
        top_regions = self._top_regions(event)
        return top_regions[:limit]

    def get_top_cities(self, site_id, start: date, end: date, limit: int = 10):
        event = EventService().get_site_events_date_range(site_id, start, end)
        
        top_cities = self._top_cities(event)
        return top_cities[:limit]
    
    # Helpers for any specific day except current (incomplete) day
    def get_anyday_site_summary(self, site_id: int, day: date):
        stats = DailySiteStats.objects.filter(
            site_id=site_id,
            date=day
        )
        summary = self._site_summary(stats)
        return summary

    def get_anyday_timeseries(self, site_id: int, day: date):
        """Return one row per hour for that day"""
        data = (EventService().get_site_events(site_id, day)
                .annotate(hour=TruncHour('timestamp'))
                .values('hour')
                .annotate(
                    visitors=Count('visitor_id', distinct=True),
                    pageviews=Count('id'),
                )
                .order_by('hour')
        )
        timeseries = []
        for event in data:
            start = event['hour'] 
            end = start + timedelta(hours=1)
            session_metrics = AggregationService().get_session_metrics(site_id, start_dt=start, end_dt=end)
            sessions = session_metrics['total_visits']
            event['bounce_rate'] = round(session_metrics['single_page_sessions'] / sessions * 100) if sessions else 0
            event['avg_durations_seconds'] = round(session_metrics['total_duration_seconds'] / sessions * 100) if sessions else 0
            event['views_per_visit'] = round(session_metrics['total_pageviews_in_sessions'] / sessions * 100, 2) if sessions else 0.00
            timeseries.append(event)
        return timeseries
    
    def get_anyday_top_pages(self, site_id: int, day: date, limit: int =10):
        stats = DailyPageStats.objects.filter(
            site_id=site_id,
            date=day
        )
        top_pages = self._top_pages(stats)
        return top_pages[:limit]
    
    def get_anyday_top_referrers(self, site_id: int, day: date, limit: int =10):
        stats = DailyReferrerStats.objects.filter(
            site_id=site_id,
            date=day,
        )
        top_referrers = self._top_referrers(stats)
        return top_referrers[:limit]

    def get_anyday_country_breakdown(self, site_id: int, day: date):
        stats = DailyCountryStats.objects.filter(
            site_id=site_id,
            date=day,
        )
        country_breakdown = self._country_breakdown(stats)
        return country_breakdown

    def get_anyday_device_breakdown(self, site_id: int, day: date):
        stats = DailyDeviceStats.objects.filter(
            site_id=site_id,
            date=day,
        )
        browser_breakdown = self._device_breakdown(stats)
        return browser_breakdown

    def get_anyday_browser_breakdown(self, site_id: int, day: date):
        stats = DailyBrowserStats.objects.filter(
            site_id=site_id,
            date=day,
        )
        browser_breakdown = self._browser_breakdown(stats)
        return browser_breakdown

    def get_anyday_os_breakdown(self, site_id: int, day: date):
        stats = DailyOSStats.objects.filter(
            site_id=site_id,
            date=day,
        )
        os_breakdown = self._os_breakdown(stats)
        return os_breakdown
    
    def get_anyday_top_regions(self, site_id, day: date, limit: int = 10):
        event = EventService().get_site_events(site_id, day)
        
        top_regions = self._top_regions(event)
        return top_regions[:limit]

    def get_anyday_top_cities(self, site_id, day: date, limit: int = 10):
        event = EventService().get_site_events(site_id, day)
        
        top_cities = self._top_cities(event)
        return top_cities[:limit]

    # Raw‑event helpers for the current (incomplete) day
    def get_today_site_summary(self, site_id):
        today = timezone.now().date()
        stats = EventService().get_site_events(site_id, today).aggregate(
            visitors=Count('visitor_id', distinct=True),
            pageviews=Count('id'),
        )
        session_metrics = AggregationService().get_session_metrics(site_id, day=today)
        sessions = session_metrics['total_visits']

        stats['bounce_rate'] = round(session_metrics['single_page_sessions'] / sessions * 100) if sessions else 0
        stats['avg_durations_seconds'] = round(session_metrics['total_duration_seconds'] / sessions * 100) if sessions else 0
        stats['views_per_visit'] = round(session_metrics['total_pageviews_in_sessions'] / sessions * 100, 2) if sessions else 0.00

        return stats

    def get_today_timeseries(self, site_id: int):
        """Return one row per hour for today."""
        today = date.today()
        data = (EventService().get_site_events(site_id, today)
                .annotate(hour=TruncHour('timestamp'))
                .values('hour')
                .annotate(
                    visitors=Count('visitor_id', distinct=True),
                    pageviews=Count('id'),
                )
                .order_by('hour')
        )
        timeseries = []
        for event in data:
            start = event['hour'] 
            end = start + timedelta(hours=1)
            session_metrics = AggregationService().get_session_metrics(site_id, start_dt=start, end_dt=end)
            sessions = session_metrics['total_visits']
            event['bounce_rate'] = round(session_metrics['single_page_sessions'] / sessions * 100) if sessions else 0
            event['avg_durations_seconds'] = round(session_metrics['total_duration_seconds'] / sessions * 100) if sessions else 0
            event['views_per_visit'] = round(session_metrics['total_pageviews_in_sessions'] / sessions * 100, 2) if sessions else 0.00
            timeseries.append(event)
        return timeseries

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
        
        top_regions = self._top_regions(event)
        return top_regions[:limit]


    def get_today_top_cities(self, site_id, limit: int = 10):
        today = date.today()
        event = EventService().get_site_events(site_id, today)
        
        top_cities = self._top_cities(event)
        return top_cities[:limit]


    def get_hourly_site_summary(self, site_id: int, start_dt: datetime, end_dt: datetime):
        stats = EventService().get_site_events_hour_range(site_id, start_dt, end_dt).aggregate(
            visitors=Count('visitor_id', distinct=True),
            pageviews=Count('id'),
        )
        session_metrics = AggregationService().get_session_metrics(site_id, start_dt=start_dt, end_dt=end_dt)
        sessions = session_metrics['total_visits']
        
        stats['bounce_rate'] = round(session_metrics['single_page_sessions'] / sessions * 100) if sessions else 0
        stats['avg_durations_seconds'] = round(session_metrics['total_duration_seconds'] / sessions * 100) if sessions else 0
        stats['views_per_visit'] = round(session_metrics['total_pageviews_in_sessions'] / sessions * 100, 2) if sessions else 0.00
    
        return stats
    
    def get_hourly_timeseries(self, site_id: int, start_dt: datetime, end_dt: datetime):
        """
        Return one row per hour for the past 24 hours.
        """
        data = (EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
            .annotate(hour=TruncHour('timestamp'))
            .values('hour')
            .annotate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            .order_by('hour')
        )
        timeseries = []
        for event in data:
            start = event['hour'] 
            end = start + timedelta(hours=1)
            session_metrics = AggregationService().get_session_metrics(site_id, start_dt=start, end_dt=end)
            sessions = session_metrics['total_visits']
            event['bounce_rate'] = round(session_metrics['single_page_sessions'] / sessions * 100) if sessions else 0
            event['avg_durations_seconds'] = round(session_metrics['total_duration_seconds'] / sessions * 100) if sessions else 0
            event['views_per_visit'] = round(session_metrics['total_pageviews_in_sessions'] / sessions * 100, 2) if sessions else 0.00
            timeseries.append(event)
        return timeseries

    def get_hourly_top_pages(self, site_id: int, start_dt: datetime, end_dt: datetime, limit: int = 10):
        return (
            EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
            .values('url')
            .annotate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            .order_by('-pageviews')[:limit]
        )

    def get_hourly_top_referrers(self, site_id: int, start_dt: datetime, end_dt: datetime, limit: int = 10):
        return (
            EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
            .values('source', 'medium')
            .annotate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            .order_by('-pageviews')[:limit]
        )

    def get_hourly_country_breakdown(self, site_id: int, start_dt: datetime, end_dt: datetime):
        return (
            EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
            .values('country')
            .annotate(visitors=Count('visitor_id', distinct=True))
            .order_by('-visitors')
        )

    def get_hourly_device_breakdown(self, site_id: int, start_dt: datetime, end_dt: datetime):
        return (EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
                .values('device_type')
                .annotate(visitors=Sum('visitors'))
                .order_by('-visitors'))

    def get_hourly_browser_breakdown(self, site_id: int, start_dt: datetime, end_dt: datetime):
        return (EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
                .values('browser')
                .annotate(visitors=Sum('visitors'))
                .order_by('-visitors'))

    def get_hourly_os_breakdown(self, site_id: int, start_dt: datetime, end_dt: datetime):
        return (EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
                .values('os')
                .annotate(visitors=Sum('visitors'))
                .order_by('-visitors'))
    
    def get_hourly_top_regions(self, site_id, start_dt: datetime, end_dt: datetime, limit: int = 10):
        event = EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
        
        top_regions = self._top_regions(event)
        return top_regions[:limit]


    def get_hourly_top_cities(self, site_id, start_dt: datetime, end_dt: datetime, limit: int = 10):
        event = EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
        
        top_cities = self._top_cities(event)
        return top_cities[:limit]
    # def get_realtime_site_summary(self, site_id: int, minutes: int = 5):
    #     """
    #     Return visitors and pageviews in the last `minutes` minutes.
    #     """
    #     since = timezone.now() - timedelta(minutes=minutes)
    #     data = EventService().get_site_events_realtime(site_id, since).aggregate(
    #         visitors=Count('visitor_id', distinct=True),
    #         pageviews=Count('id'),
    #     )
    #     return {
    #         'visitors': data['visitors'] or 0,
    #         'pageviews': data['pageviews'] or 0,
    #         'last_updated': timezone.now().isoformat(),
    #     }