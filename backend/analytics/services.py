from datetime import date, timedelta, datetime
from django.db import transaction
from django.db.models import Sum, Count
from django.db.models.manager import BaseManager
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
from common.utils import get_local_day_utc_range, get_site_timezone
from django.db.models.functions import TruncHour, TruncMonth, TruncYear
from urllib.parse import urlparse, urlunparse


class AggregationService:
    """Populate daily summary tables for a given site and date."""

    def _clean_path(self, url: str):
        """Strip query parameters from url"""
        parsed = urlparse(url)
        return urlunparse(parsed._replace(query=''))
    
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

        for _, timestamps in visitor_events.items():

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
            'total_duration_seconds': int(total_duration.total_seconds()),
            'total_pageviews_in_sessions': total_pageviews_in_sessions,
        }

    def aggregate_date(self, site, day: date):
        start_utc, end_utc = get_local_day_utc_range(site, day)
        events = EventService().get_site_events_timestamp(site.id, start_utc, end_utc)
        session_metrics = self.get_session_metrics(site.id, start_dt=start_utc, end_dt=end_utc)

        if not events.exists():
            return

        with transaction.atomic():
            # Site totals
            site_data = events.aggregate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            DailySiteStats.objects.update_or_create(
                site_id=site.id,
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
            path_pageviews = defaultdict(int)      # path -> total pageviews
            path_visitors = defaultdict(set)       # path -> set of visitor IDs

            for row in events.values('visitor_id', 'url'):
                path = self._clean_path(row['url'])
                path_pageviews[path] += 1
                path_visitors[path].add(row['visitor_id'])

            instances = [DailyPageStats(
                site=site,
                date=day,
                url=path,
                visitors=len(visitors),
                pageviews=pageviews,
            ) for path, pageviews in path_pageviews.items()
            for visitors in [path_visitors[path]]
            ]
            DailyPageStats.objects.bulk_create(
                instances,
                update_conflicts=True,
                unique_fields=['site', 'date', 'url'],
                update_fields=['visitors', 'pageviews']
            )

            # Referrer stats
            ref_pageviews = defaultdict(int)
            ref_visitors = defaultdict(set)

            for row in events.values('visitor_id', 'source', 'medium'):
                key = (row['source'] or 'Direct', row['medium'] or 'none')
                ref_pageviews[key] += 1
                ref_visitors[key].add(row['visitor_id'])
            
            instances = [
                DailyReferrerStats(
                    site_id=site.id,
                    date=day,
                    source=source,
                    medium=medium,
                    visitors=len(ref_visitors[(source, medium)]),
                    pageviews=ref_pageviews[(source, medium)]
                )
                for source, medium in ref_pageviews
            ]
            DailyReferrerStats.objects.bulk_create(
                instances,
                update_conflicts=True,
                unique_fields=['site', 'date', 'source', 'medium'],
                update_fields=['visitors', 'pageviews']
            )

            # Country stats
            country_visitors = defaultdict(set)
            for row in events.values('visitor_id', 'country'):
                if row['country']:
                    country_visitors[row['country']].add(row['visitor_id'])

            instances = [
                DailyCountryStats(
                    site_id=site.id,
                    date=day,
                    country=country,
                    visitors=len(visitors),
                )
                for country, visitors in country_visitors.items()
            ]
            DailyCountryStats.objects.bulk_create(
                instances,
                update_conflicts=True,
                unique_fields=['site', 'date', 'country'],
                update_fields=['visitors']
            )

            # Device stats
            device_visitors = defaultdict(set)
            for row in events.values('visitor_id', 'device_type'):
                if row['device_type']:
                    device_visitors[row['device_type']].add(row['visitor_id'])

            instances = [
                DailyDeviceStats(
                    site_id=site.id,
                    date=day,
                    device_type=device_type,
                    visitors=len(visitors)
                )
                for device_type, visitors in device_visitors.items()
            ]
            DailyDeviceStats.objects.bulk_create(
                instances,
                update_conflicts=True,
                unique_fields=['site', 'date', 'device_type'],
                update_fields=['visitors'],
            )

            # Browser stats
            browser_visitors = defaultdict(set)
            for row in events.values('visitor_id', 'browser'):
                if row['browser']:
                    browser_visitors[row['browser']].add(row['visitor_id'])

            instances = [
                DailyBrowserStats(
                    site=site,
                    date=day,
                    browser=browser,
                    visitors=len(visitors),
                )
                for browser, visitors in browser_visitors.items()
                ]
            DailyBrowserStats.objects.bulk_create(
                instances,
                update_conflicts=True,
                unique_fields=['site', 'date', 'browser'],
                update_fields=['visitors'],
            )

            # OS stats
            os_visitors = defaultdict(set)
            for row in events.values('visitor_id', 'os'):
                if row['os']:
                    os_visitors[row['os']].add(row['visitor_id'])

            instances = [
                DailyOSStats(
                    site=site,
                    date=day,
                    os=os,
                    visitors=len(visitors),
                )
                for os, visitors in os_visitors.items()
            ]
            DailyOSStats.objects.bulk_create(
                instances,
                update_conflicts=True,
                unique_fields=['site', 'date', 'os'],
                update_fields=['visitors'],
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
        summary['avg_duration_seconds'] = round(summary['total_duration_seconds'] / sessions) if sessions else 0
        summary['views_per_visit'] = round(summary['total_pageviews_in_sessions'] / sessions, 2) if sessions else 0.00

        del summary['total_pageviews_in_sessions']
        del summary['total_duration_seconds']
        del summary['single_page_sessions']

        return summary

    def _top_pages(self, stat: BaseManager[DailyPageStats]):
        return stat.values('url').annotate(
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

    def _top_regions(self, event):
        return event.exclude(region='').values('region').annotate(
            visitors=Count('visitor_id', distinct=True),
        ).order_by('-visitors')
    
    def _top_cities(self, event):
        return event.exclude(city='').values('city').annotate(
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

    def get_daily_timeseries(self, site_id: int, start_date: date, end_date: date):
        """ Return daily data points for a date range"""
        data = DailySiteStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date
        ).values('date', 'visitors', 'pageviews', 
                 'total_visits', 'single_page_sessions', 'total_duration_seconds', 
                 'total_pageviews_in_sessions').order_by('date')
        timeseries = []
        for event in data:
            sessions = event['total_visits']
            event['day'] = event['date']
            event['bounce_rate'] = round(event['single_page_sessions'] / sessions * 100) if sessions else 0
            event['avg_duration_seconds'] = round(event['total_duration_seconds'] / sessions) if sessions else 0
            event['views_per_visit'] = round(event['total_pageviews_in_sessions'] / sessions, 2) if sessions else 0.00
            
            del event['date']
            del event['single_page_sessions']
            del event['total_duration_seconds']
            del event['total_pageviews_in_sessions']
            
            timeseries.append(event)
        return timeseries

    def get_top_pages(self, site_id: int, start_date: date, end_date: date):
        stats = DailyPageStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        )
        top_pages = self._top_pages(stats)
        return top_pages

    def get_top_referrers(self, site_id: int, start_date: date, end_date: date):
        stats = DailyReferrerStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        )
        top_referrers = self._top_referrers(stats)
        return top_referrers

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
    
    
    def get_top_regions(self, site_id, start: date, end: date):
        event = EventService().get_site_events_date_range(site_id, start, end)
        
        top_regions = self._top_regions(event)
        return top_regions

    def get_top_cities(self, site_id, start: date, end: date):
        event = EventService().get_site_events_date_range(site_id, start, end)
        
        top_cities = self._top_cities(event)
        return top_cities
    
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
            event['total_visits'] = sessions
            event['bounce_rate'] = round(session_metrics['single_page_sessions'] / sessions * 100) if sessions else 0
            event['avg_duration_seconds'] = round(session_metrics['total_duration_seconds'] / sessions) if sessions else 0
            event['views_per_visit'] = round(session_metrics['total_pageviews_in_sessions'] / sessions, 2) if sessions else 0.00
            timeseries.append(event)
        return timeseries
    
    def get_anyday_top_pages(self, site_id: int, day: date):
        stats = DailyPageStats.objects.filter(
            site_id=site_id,
            date=day
        )
        top_pages = self._top_pages(stats)
        return top_pages
    
    def get_anyday_top_referrers(self, site_id: int, day: date):
        stats = DailyReferrerStats.objects.filter(
            site_id=site_id,
            date=day,
        )
        top_referrers = self._top_referrers(stats)
        return top_referrers

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
    
    def get_anyday_top_regions(self, site_id, day: date):
        event = EventService().get_site_events(site_id, day)
        
        top_regions = self._top_regions(event)
        return top_regions

    def get_anyday_top_cities(self, site_id, day: date):
        event = EventService().get_site_events(site_id, day)
        
        top_cities = self._top_cities(event)
        return top_cities

    # Raw‑event helpers for the current (incomplete) day
    def get_today_site_summary(self, site):
        local_today = timezone.now().astimezone(get_site_timezone(site)).date()
        start_utc, end_utc = get_local_day_utc_range(site, local_today)

        stats = EventService().get_site_events_timestamp(site.id, start_utc, end_utc).aggregate(
            visitors=Count('visitor_id', distinct=True),
            pageviews=Count('id'),
        )
        session_metrics = AggregationService().get_session_metrics(site.id, start_dt=start_utc, end_dt=end_utc)
        sessions = session_metrics['total_visits']

        stats['total_visits'] = sessions
        stats['bounce_rate'] = round(session_metrics['single_page_sessions'] / sessions * 100) if sessions else 0
        stats['avg_duration_seconds'] = round(session_metrics['total_duration_seconds'] / sessions) if sessions else 0
        stats['views_per_visit'] = round(session_metrics['total_pageviews_in_sessions'] / sessions, 2) if sessions else 0.00

        return stats

    def get_today_timeseries(self, site):
        """Return one row per hour for today."""
        local_today = timezone.now().astimezone(get_site_timezone(site)).date()
        start_utc, end_utc = get_local_day_utc_range(site, local_today)

        data = (EventService().get_site_events_timestamp(site.id, start_utc, end_utc)
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
            session_metrics = AggregationService().get_session_metrics(site.id, start_dt=start, end_dt=end)
            sessions = session_metrics['total_visits']
            event['total_visits'] = sessions
            event['bounce_rate'] = round(session_metrics['single_page_sessions'] / sessions * 100) if sessions else 0
            event['avg_duration_seconds'] = round(session_metrics['total_duration_seconds'] / sessions) if sessions else 0
            event['views_per_visit'] = round(session_metrics['total_pageviews_in_sessions'] / sessions, 2) if sessions else 0.00
            timeseries.append(event)
        return timeseries

    def get_today_top_pages(self, site):
        local_today = timezone.now().astimezone(get_site_timezone(site)).date()
        start_utc, end_utc = get_local_day_utc_range(site, local_today)

        return (
            EventService().get_site_events_timestamp(site.id, start_utc, end_utc)
            .values('url')
            .annotate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            .order_by('-pageviews')
        )

    def get_today_top_referrers(self, site):
        local_today = timezone.now().astimezone(get_site_timezone(site)).date()
        start_utc, end_utc = get_local_day_utc_range(site, local_today)

        return (
            EventService().get_site_events_timestamp(site.id, start_utc, end_utc)
            .values('source', 'medium')
            .annotate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            .order_by('-pageviews')
        )

    def get_today_country_breakdown(self, site):
        local_today = timezone.now().astimezone(get_site_timezone(site)).date()
        start_utc, end_utc = get_local_day_utc_range(site, local_today)

        return (
            EventService().get_site_events_timestamp(site.id, start_utc, end_utc)
            .values('country')
            .annotate(visitors=Count('visitor_id', distinct=True))
            .order_by('-visitors')
        )

    def get_today_device_breakdown(self, site):
        local_today = timezone.now().astimezone(get_site_timezone(site)).date()
        start_utc, end_utc = get_local_day_utc_range(site, local_today)

        return (EventService().get_site_events_timestamp(site.id, start_utc, end_utc)
                .values('device_type')
                .annotate(visitors=Count('visitor_id', distinct=True))
                .order_by('-visitors'))

    def get_today_browser_breakdown(self, site):
        local_today = timezone.now().astimezone(get_site_timezone(site)).date()
        start_utc, end_utc = get_local_day_utc_range(site, local_today)

        return (EventService().get_site_events_timestamp(site.id, start_utc, end_utc)
                .values('browser')
                .annotate(visitors=Count('visitor_id', distinct=True))
                .order_by('-visitors'))

    def get_today_os_breakdown(self, site):
        local_today = timezone.now().astimezone(get_site_timezone(site)).date()
        start_utc, end_utc = get_local_day_utc_range(site, local_today)

        return (EventService().get_site_events_timestamp(site.id, start_utc, end_utc)
                .values('os')
                .annotate(visitors=Count('visitor_id', distinct=True))
                .order_by('-visitors'))
    
    def get_today_top_regions(self, site):
        local_today = timezone.now().astimezone(get_site_timezone(site)).date()
        start_utc, end_utc = get_local_day_utc_range(site, local_today)

        event = EventService().get_site_events_timestamp(site.id, start_utc, end_utc)
        
        top_regions = self._top_regions(event)
        return top_regions


    def get_today_top_cities(self, site):
        local_today = timezone.now().astimezone(get_site_timezone(site)).date()
        start_utc, end_utc = get_local_day_utc_range(site, local_today)

        event = EventService().get_site_events_timestamp(site.id, start_utc, end_utc)
        
        top_cities = self._top_cities(event)
        return top_cities


    def get_hourly_site_summary(self, site_id: int, start_dt: datetime, end_dt: datetime):
        stats = EventService().get_site_events_hour_range(site_id, start_dt, end_dt).aggregate(
            visitors=Count('visitor_id', distinct=True),
            pageviews=Count('id'),
        )
        session_metrics = AggregationService().get_session_metrics(site_id, start_dt=start_dt, end_dt=end_dt)
        sessions = session_metrics['total_visits']
        
        stats['total_visits'] = sessions
        stats['bounce_rate'] = round(session_metrics['single_page_sessions'] / sessions * 100) if sessions else 0
        stats['avg_duration_seconds'] = round(session_metrics['total_duration_seconds'] / sessions) if sessions else 0
        stats['views_per_visit'] = round(session_metrics['total_pageviews_in_sessions'] / sessions, 2) if sessions else 0.00
    
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
            event['total_visits'] = sessions
            event['bounce_rate'] = round(session_metrics['single_page_sessions'] / sessions * 100) if sessions else 0
            event['avg_duration_seconds'] = round(session_metrics['total_duration_seconds'] / sessions) if sessions else 0
            event['views_per_visit'] = round(session_metrics['total_pageviews_in_sessions'] / sessions, 2) if sessions else 0.00
            timeseries.append(event)
        return timeseries

    def get_hourly_top_pages(self, site_id: int, start_dt: datetime, end_dt: datetime):
        return (
            EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
            .values('url')
            .annotate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            .order_by('-pageviews')
        )

    def get_hourly_top_referrers(self, site_id: int, start_dt: datetime, end_dt: datetime):
        return (
            EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
            .values('source', 'medium')
            .annotate(
                visitors=Count('visitor_id', distinct=True),
                pageviews=Count('id'),
            )
            .order_by('-pageviews')
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
                .annotate(visitors=Count('visitor_id', distinct=True))
                .order_by('-visitors'))

    def get_hourly_browser_breakdown(self, site_id: int, start_dt: datetime, end_dt: datetime):
        return (EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
                .values('browser')
                .annotate(visitors=Count('visitor_id', distinct=True))
                .order_by('-visitors'))

    def get_hourly_os_breakdown(self, site_id: int, start_dt: datetime, end_dt: datetime):
        return (EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
                .values('os')
                .annotate(visitors=Count('visitor_id', distinct=True))
                .order_by('-visitors'))
    
    def get_hourly_top_regions(self, site_id, start_dt: datetime, end_dt: datetime):
        event = EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
        
        top_regions = self._top_regions(event)
        return top_regions


    def get_hourly_top_cities(self, site_id, start_dt: datetime, end_dt: datetime):
        event = EventService().get_site_events_hour_range(site_id, start_dt, end_dt)
        
        top_cities = self._top_cities(event)
        return top_cities

    def get_monthly_timeseries(self, site_id: int, start_date: date, end_date: date):
        """
        Return one row per month with summed metrics.
        start_date / end_date are date objects (first/last day of the range).
        """
        rows = (
            DailySiteStats.objects
            .filter(site_id=site_id, date__gte=start_date, date__lte=end_date)
            .annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(
                visitors=Sum('visitors'),
                pageviews=Sum('pageviews'),
                total_visits=Sum('total_visits'),
                single_page_sessions=Sum('single_page_sessions'),
                total_duration_seconds=Sum('total_duration_seconds'),
                total_pageviews_in_sessions=Sum('total_pageviews_in_sessions'),
            )
            .order_by('month')
        )

        timeseries = []
        for row in rows:
            sessions = row['total_visits']
            row['total_visits'] = sessions
            row['bounce_rate'] = round(row['single_page_sessions'] / sessions * 100) if sessions else 0
            row['avg_duration_seconds'] = round(row['total_duration_seconds'] / sessions) if sessions else 0
            row['views_per_visit'] = round(row['total_pageviews_in_sessions'] / sessions, 2) if sessions else 0.00
            
            del row['single_page_sessions']
            del row['total_pageviews_in_sessions']
            del row['total_duration_seconds']
            
            timeseries.append(row)

        return timeseries
    
    def get_yearly_timeseries(self, site_id: int, start_date: date, end_date: date):
        rows = (
            DailySiteStats.objects
            .filter(site_id=site_id, date__gte=start_date, date__lte=end_date)
            .annotate(year=TruncYear('date'))
            .values('year')
            .annotate(
                visitors=Sum('visitors'),
                pageviews=Sum('pageviews'),
                total_visits=Sum('total_visits'),
                single_page_sessions=Sum('single_page_sessions'),
                total_duration_seconds=Sum('total_duration_seconds'),
                total_pageviews_in_sessions=Sum('total_pageviews_in_sessions'),
            )
            .order_by('year')
        )

        timeseries = []
        for row in rows:
            sessions = row['total_visits']
            row['bounce_rate'] = round(row['single_page_sessions'] / sessions * 100) if sessions else 0
            row['avg_duration_seconds'] = round(row['total_duration_seconds'] / sessions) if sessions else 0
            row['views_per_visit'] = round(row['total_pageviews_in_sessions'] / sessions, 2) if sessions else 0.00
            
            del row['single_page_sessions']
            del row['total_pageviews_in_sessions']
            del row['total_duration_seconds']
            
            timeseries.append(row)

        return timeseries
