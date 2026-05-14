from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from common.response import api_response
from sites.services import SiteService
from .services import StatsQueryService
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from common.openapi import envelope_success
from django.utils import timezone


class BaseStatsView(APIView):
    """
    Shared helpers for all analytics views:
    - Ownership check
    - Date range parsing from query parameters
    """
    permission_classes = [IsAuthenticated]

    def get_site(self, site_id):
        """Returns the site if it exists and belongs to the user, otherwise None."""
        site = SiteService().get_site_by_id(site_id)
        if not site or site.user_id != self.request.user.id:
            return None
        return site

    def parse_date_range(self):
        """Parse query params."""
        try:
            if self.request.query_params.get('interval') == '24h':
                return {'hour': '24h'}
            elif self.request.query_params.get('interval') == 'custom':
                if self.request.query_params.get('start') and self.request.query_params.get('end'):
                    start = date.fromisoformat(self.request.query_params['start'])
                    end = date.fromisoformat(self.request.query_params['end'])
                    return {'range': {'start': start, 'end': end}}
            elif self.request.query_params.get('interval') == 'day':
                if self.request.query_params.get('day'):
                    day = date.fromisoformat(self.request.query_params['day'])
                    if day != date.today():
                        return {'day': day}
                    else:
                        return {'today': day}
            elif self.request.query_params.get('interval') == 'month-to-date':
                pass
            elif self.request.query_params.get('interval') == 'year-to-date':
                pass
            elif self.request.query_params.get('interval') == '91d':
                start = timezone.now() - timedelta(days=91)
                end = timezone.now() - timedelta(days=1)
                return {'range': {'start': start, 'end': end}}
            elif self.request.query_params.get('interval') == '31d':
                start = timezone.now() - timedelta(days=31)
                end =  timezone.now() - timedelta(days=1)
                return {'range': {'start': start, 'end': end}}
            else:
                return {}
        except ValueError as e:
            raise ValueError(str(e))
        return {}


    def get_limit(self, default=10):
        """Extract limit from query params, clamped to 1-100."""
        try:
            limit = int(self.request.query_params.get('limit', default))
            return max(1, min(limit, 100))
        except (ValueError, TypeError):
            return default


# Aggregated endpoints

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval (day, 24h or custom).
            day: follow up with day query params and pass in the specific date,
            24h: return stat from 24 hours ago,
            custom: follow up with a start and end query params to define a date range,
            year-to-date: return stat from beginning of the current year, 
            month-to-date: return start from the beginning of the current month,
            31d: return stat from the last 31 days, excluding current day,
            91d: return stat from the last 91 days, excluding current day""",
            required=False,
        ),
        OpenApiParameter(
            name='day',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        )
    ],
    summary="Get summary stats for a given date or date range.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date. Interval must be set to custom
    Pass both start and end params for date ranges. Interval must be set to day
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get summary stats.""",
    responses=envelope_success,
)
class SummaryView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_site_summary(site.id, date_arg['range']['start'], date_arg['range'['end']])
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_site_summary(site.id, date_arg['day'])
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_site_summary(site.id, start_dt=end, end_dt=now)
        else:
            stats = StatsQueryService().get_today_site_summary(site.id)
        
        return api_response(status.HTTP_200_OK, data=stats)

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval (day, 24h or custom).
            day: follow up with day query params and pass in the specific date,
            24h: return stat from 24 hours ago,
            custom: follow up with a start and end query params to define a date range,
            year-to-date: return stat from beginning of the current year, 
            month-to-date: return start from the beginning of the current month,
            31d: return stat from the last 31 days, excluding current day,
            91d: return stat from the last 91 days, excluding current day """,
            required=False,
        ),
        OpenApiParameter(
            name='day',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        )
    ],
    summary="Get timeseries stats for a given date or date range.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date. Interval must be set to custom
    Pass both start and end params for date ranges. Interval must be set to day
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get timeseries stats for visualization (graph plotting, etc).
""",
    responses=envelope_success,
)
class TimeseriesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_timeseries(site.id, date_arg['range']['start'], date_arg['range']['end'])
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_timeseries(site.id, date_arg['day'])
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_timeseries(site.id, start_dt=end, end_dt=now)
        else:
            stats = StatsQueryService().get_today_timeseries(site.id)

        return api_response(status.HTTP_200_OK, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval (day, 24h or custom).
            day: follow up with day query params and pass in the specific date,
            24h: return stat from 24 hours ago,
            custom: follow up with a start and end query params to define a date range,
            year-to-date: return stat from beginning of the current year, 
            month-to-date: return start from the beginning of the current month,
            31d: return stat from the last 31 days, excluding current day,
            91d: return stat from the last 91 days, excluding current day """,
            required=False,
        ),
        OpenApiParameter(
            name='day',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
       OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Pass in an int value",
            required=False,
        ),
    ],
    summary="Get top pages viewed stats for a given date or date range.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date. Interval must be set to custom
    Pass both start and end params for date ranges. Interval must be set to day
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get top pages viewed.
""",
    responses=envelope_success,
)
class TopPagesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        limit = self.get_limit(10)
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_top_pages(site.id, date_arg['range']['start'], date_arg['range']['end'], limit)
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_top_pages(site.id, date_arg['day'], limit)
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_top_pages(site.id, start_dt=end, end_dt=now, limit=limit)
        else:
            stats = StatsQueryService().get_today_top_pages(site.id, limit)

        return api_response(status.HTTP_200_OK, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval (day, 24h or custom).
            day: follow up with day query params and pass in the specific date,
            24h: return stat from 24 hours ago,
            custom: follow up with a start and end query params to define a date range,
            year-to-date: return stat from beginning of the current year, 
            month-to-date: return start from the beginning of the current month,
            31d: return stat from the last 31 days, excluding current day,
            91d: return stat from the last 91 days, excluding current day """,
            required=False,
        ),
        OpenApiParameter(
            name='day',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
       OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Pass in an int value",
            required=False,
        ),
    ],
    summary="Get top referrers stats for a given date or date range.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date. Interval must be set to custom
    Pass both start and end params for date ranges. Interval must be set to day
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.    
    Get top referrers stats i.e source and medium e.g Organic search, Google.
    """,
    responses=envelope_success,
)
class TopReferrersView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        limit = self.get_limit(10)
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_top_referrers(site.id, date_arg['range']['start'], date_arg['range']['end'], limit)
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_top_referrers(site.id, date_arg['day'], limit)
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_top_referrers(site.id, start_dt=end, end_dt=now, limit=limit)
        else:
            stats = StatsQueryService().get_today_top_referrers(site.id, limit)
        return api_response(status.HTTP_200_OK, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval (day, 24h or custom).
            day: follow up with day query params and pass in the specific date,
            24h: return stat from 24 hours ago,
            custom: follow up with a start and end query params to define a date range,
            year-to-date: return stat from beginning of the current year, 
            month-to-date: return start from the beginning of the current month,
            31d: return stat from the last 31 days, excluding current day,
            91d: return stat from the last 91 days, excluding current day """,
            required=False,
        ),
        OpenApiParameter(
            name='day',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        )
    ],
    summary="Get countries stats for a given date or date range.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date. Interval must be set to custom
    Pass both start and end params for date ranges. Interval must be set to day
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get countries visiting the site.
""",
    responses=envelope_success,
)
class CountriesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_country_breakdown(site.id, date_arg['range']['start'], date_arg['range']['end'])
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_country_breakdown(site.id, date_arg['day'])
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_country_breakdown(site.id, start_dt=end, end_dt=now)
        else:
            stats = StatsQueryService().get_today_country_breakdown(site.id)

        return api_response(status.HTTP_200_OK, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval (day, 24h or custom).
            day: follow up with day query params and pass in the specific date,
            24h: return stat from 24 hours ago,
            custom: follow up with a start and end query params to define a date range,
            year-to-date: return stat from beginning of the current year, 
            month-to-date: return start from the beginning of the current month,
            31d: return stat from the last 31 days, excluding current day,
            91d: return stat from the last 91 days, excluding current day """,
            required=False,
        ),
        OpenApiParameter(
            name='day',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        )
    ],
    summary="Get devices stats for a given date or date range.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date. Interval must be set to custom
    Pass both start and end params for date ranges. Interval must be set to day
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get devices used to visit the site.
""",
    responses=envelope_success,
)
class DevicesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_device_breakdown(site.id, date_arg['range']['start'], date_arg['range']['end'])
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_device_breakdown(site.id, date_arg['day'])
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_device_breakdown(site.id, start_dt=end, end_dt=now)
        else:
            stats = StatsQueryService().get_today_device_breakdown(site.id)

        return api_response(status.HTTP_200_OK, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval (day, 24h or custom).
            day: follow up with day query params and pass in the specific date,
            24h: return stat from 24 hours ago,
            custom: follow up with a start and end query params to define a date range,
            year-to-date: return stat from beginning of the current year, 
            month-to-date: return start from the beginning of the current month,
            31d: return stat from the last 31 days, excluding current day,
            91d: return stat from the last 91 days, excluding current day """,
            required=False,
        ),
        OpenApiParameter(
            name='day',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        )
    ],
    summary="Get browsers stats for a given date or date range.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date. Interval must be set to custom
    Pass both start and end params for date ranges. Interval must be set to day
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get browsers used to visit the site.
""",
    responses=envelope_success,
)
class BrowsersView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_browser_breakdown(site.id, date_arg['range']['start'], date_arg['range']['end'])
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_browser_breakdown(site.id, date_arg['day'])
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_browser_breakdown(site.id, start_dt=end, end_dt=now)
        else:
            stats = StatsQueryService().get_today_browser_breakdown(site.id)

        return api_response(status.HTTP_200_OK, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval (day, 24h or custom).
            day: follow up with day query params and pass in the specific date,
            24h: return stat from 24 hours ago,
            custom: follow up with a start and end query params to define a date range,
            year-to-date: return stat from beginning of the current year, 
            month-to-date: return start from the beginning of the current month,
            31d: return stat from the last 31 days, excluding current day,
            91d: return stat from the last 91 days, excluding current day """,
            required=False,
        ),
        OpenApiParameter(
            name='day',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        )
    ],
    summary="Get operating system stats for a given date or date range.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date. Interval must be set to custom
    Pass both start and end params for date ranges. Interval must be set to day
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get operating systems used when visiting the site.
""",
    responses=envelope_success,
)
class OSView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_os_breakdown(site.id, date_arg['range']['start'], date_arg['range']['end'])
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_os_breakdown(site.id, date_arg['day'])
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_os_breakdown(site.id, start_dt=end, end_dt=now)
        else:
            stats = StatsQueryService().get_today_os_breakdown(site.id)

        return api_response(status.HTTP_200_OK, data=list(stats))


# On‑demand endpoints (from raw Event table)

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval (day, 24h or custom).
            day: follow up with day query params and pass in the specific date,
            24h: return stat from 24 hours ago,
            custom: follow up with a start and end query params to define a date range,
            year-to-date: return stat from beginning of the current year, 
            month-to-date: return start from the beginning of the current month,
            31d: return stat from the last 31 days, excluding current day,
            91d: return stat from the last 91 days, excluding current day """,
            required=False,
        ),
        OpenApiParameter(
            name='day',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
       OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Pass in an int value",
            required=False,
        ),
    ],
    summary="Get top regions stats for a given date or date range.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date. Interval must be set to custom
    Pass both start and end params for date ranges. Interval must be set to day
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get top regions visiting the site.
""",
    responses=envelope_success,
)
class TopRegionsView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        limit = self.get_limit(10)
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_top_regions(site.id, date_arg['range']['start'], date_arg['range']['end'], limit)
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_top_regions(site.id, date_arg['day'], limit)
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_top_regions(site.id, start_dt=end, end_dt=now, limit=limit)
        else:
            stats = StatsQueryService().get_today_top_regions(site.id, limit)

        return api_response(200, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval (day, 24h or custom).
            day: follow up with day query params and pass in the specific date,
            24h: return stat from 24 hours ago,
            custom: follow up with a start and end query params to define a date range,
            year-to-date: return stat from beginning of the current year, 
            month-to-date: return start from the beginning of the current month,
            31d: return stat from the last 31 days, excluding current day,
            91d: return stat from the last 91 days, excluding current day """,
            required=False,
        ),
        OpenApiParameter(
            name='day',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=False,
        ),
       OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Pass in an int value",
            required=False,
        ),
    ],
    summary="Get top cities stats for a given date or date range.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date. Interval must be set to custom
    Pass both start and end params for date ranges. Interval must be set to day
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get top cities visiting the site.
""",
    responses=envelope_success,
)
class TopCitiesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(404, message='Site not found.')

        date_arg = self.parse_date_range()
        limit = self.get_limit(10)
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_top_cities(site.id, date_arg['range']['start'], date_arg['range']['end'], limit)
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_top_cities(site.id, date_arg['day'], limit)
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_top_cities(site.id, start_dt=end, end_dt=now, limit=limit)
        else:
            stats = StatsQueryService().get_today_top_cities(site.id, limit)
        return api_response(200, data=list(stats))
