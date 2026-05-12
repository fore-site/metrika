from datetime import date
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


class AggregationService:
    """Populate daily summary tables for a given site and date."""

    def aggregate_date(self, site_id: int, day: date):
        events = EventService().get_site_events(site_id, day)

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
        return stats

    def get_timeseries(self, site_id: int, start_date: date, end_date: date):
        return DailySiteStats.objects.filter(
            site_id=site_id,
            date__gte=start_date,
            date__lte=end_date,
        ).order_by('date').values('date', 'visitors', 'pageviews')

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
        ).order_by('date').values('date', 'visitors', 'pageviews')

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
        return EventService().get_site_events(site_id, today).aggregate(
            visitors=Count('visitor_id', distinct=True),
            pageviews=Count('id'),
        )

    def get_today_timeseries(self, site_id: int):
        """Return one data point for today from raw events."""
        today = date.today()
        data = EventService().get_site_events(site_id, today).aggregate(
            visitors=Count('visitor_id', distinct=True),
            pageviews=Count('id'),
        )
        
        return [{
            'date': today.isoformat(),
            'visitors': data['visitors'] or 0,
            'pageviews': data['pageviews'] or 0,
        }]

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


    
