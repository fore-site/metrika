from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .pagination import AnalyticsPagination
from common.response import api_response
from sites.services import SiteService
from .services import StatsQueryService
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .serializers import (
    SummaryResponseSerializer,
    TimeseriesResponseSerializer,
    TopPagesResponseSerializer,
    TopReferrersResponseSerializer,
    CountriesResponseSerializer,
    DevicesResponseSerializer,
    BrowsersResponseSerializer,
    OSResponseSerializer,
    TopRegionsResponseSerializer,
    TopCitiesResponseSerializer,
)
from django.utils import timezone
import logging
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

PAGINATION_QUERY_PARAMETERS = [
    OpenApiParameter(
        name='offset',
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description="Zero-based offset into the result set. When provided, the endpoint returns a paginated response.",
        required=False,
    ),
    OpenApiParameter(
        name='limit',
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description="Maximum number of items to return. Default is 10 for dashboard previews and page size is capped by the backend.",
        required=False,
    ),
]

AUTH_RESPONSES = {
    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description='Authentication credentials were not provided.'),
    status.HTTP_403_FORBIDDEN: OpenApiResponse(description='You do not have permission to perform this action.'),
}

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
            interval = self.request.query_params.get('interval')
            if not interval:
                return {}
            if interval == '24h':
                return {'hour': '24h'}
            elif interval == 'custom':
                if not (self.request.query_params.get('start') and self.request.query_params.get('end')):
                    raise ValidationError({'detail': 'start and end query params are required when interval=custom.'})
                start = date.fromisoformat(self.request.query_params['start'])
                end = date.fromisoformat(self.request.query_params['end'])
                return {'range': {'start': start, 'end': end}}
            elif interval == 'day':
                if not self.request.query_params.get('day'):
                    raise ValidationError({'detail': 'day query param is required when interval=day.'})
                day = date.fromisoformat(self.request.query_params['day'])
                if day != date.today():
                    return {'day': day}
                return {'today': day}
            elif interval == '7d':
                start = (timezone.now() - timedelta(days=7)).date()
                end = (timezone.now() - timedelta(days=1)).date()
                return {'range': {'start': start, 'end': end}}
            elif interval == '31d':
                start = (timezone.now() - timedelta(days=31)).date()
                end = (timezone.now() - timedelta(days=1)).date()
                return {'range': {'start': start, 'end': end}}
            elif interval == 'month-to-date':
                start = date.today().replace(day=1)
                end = (timezone.now() - timedelta(days=1)).date()

                return {'range': {'start': start, 'end': end}}
            elif interval == 'year-to-date':
                start = date.today().replace(month=1, day=1)
                end = (timezone.now() - timedelta(days=1)).date()
                return {'range': {'start': start, 'end': end}}
            elif interval == '91d':
                start = (timezone.now() - timedelta(days=91)).date()
                end = (timezone.now() - timedelta(days=1)).date()
                return {'range': {'start': start, 'end': end}}
            else:
                raise ValidationError({'detail': f'Invalid interval: {interval}.'})
        except ValueError as e:
            raise ValidationError({'detail': str(e)})


    def auto_granularity(self, date_arg):
        if not date_arg:
            raise ValueError('start and end params could not be parsed.')

        start = date_arg.get('start')
        end = date_arg.get('end')

        delta = (end - start).days
        if delta == 0:
            raise ValueError('start and end params cannot be the same date.')
        elif delta <= 90:
            return 'day'
        elif delta <= 730: # 2 years
            return 'month'
        else:
            return 'year'


# Aggregated endpoints

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval:
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
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to day.",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        )
    ],
    summary="Get summary stats.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges. 
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get summary stats.""",
    responses={
        status.HTTP_200_OK: OpenApiResponse(response=SummaryResponseSerializer()),
        **AUTH_RESPONSES,
    },
    examples=[
        OpenApiExample(
            'Default example',
            value={
                'data': {
                    'visitors': 124,
                    'pageviews': 420,
                    'total_visits': 98,
                    'bounce_rate': 52.3,
                    'avg_duration_seconds': 174.6,
                    'views_per_visit': 4.29
                },
                'message': 'Summary stats retrieved successfully.'
            },
            response_only=True
        )
    ]
)
class SummaryView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        logger.info(f'date args: {date_arg}')
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_site_summary(site.id, date_arg['range'].get('start'), date_arg['range'].get('end'))
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_site_summary(site.id, date_arg['day'])
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_site_summary(site.id, start_dt=end, end_dt=now)
        else:
            stats = StatsQueryService().get_today_site_summary(site)
        
        return api_response(status.HTTP_200_OK, data=stats)

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval:
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
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to day.",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        )
    ],
    summary="Get timeseries stats.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges. 
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get timeseries stats for visualization (graph plotting, etc).
""",
    responses={
        status.HTTP_200_OK: OpenApiResponse(response=TimeseriesResponseSerializer()),
        **AUTH_RESPONSES,
    },
    examples=[
        OpenApiExample(
            'Hour precision example',
            value={
                'data': [
                    {
                        'hour': '2026-05-17T12:00:00Z',
                        'visitors': 28,
                        'pageviews': 112,
                        'total_visits': 26,
                        'bounce_rate': 48.1,
                        'avg_duration_seconds': 212.4,
                        'views_per_visit': 4.31
                    }
                ],
                'message': 'Timeseries stats retrieved successfully.',
                'meta': {
                    'precision': 'hour'
                }
            },
            response_only=True
        ),
        OpenApiExample(
            'Day precision example',
            value={
                'data': [
                    {
                        'day': '2026-05-17',
                        'visitors': 312,
                        'pageviews': 1_124,
                        'total_visits': 301,
                        'bounce_rate': 41.2,
                        'avg_duration_seconds': 198.7,
                        'views_per_visit': 3.73
                    }
                ],
                'message': 'Timeseries stats retrieved successfully.',
                'meta': {
                    'precision': 'day'
                }
            },
            response_only=True
        ),
        OpenApiExample(
            'Month precision example',
            value={
                'data': [
                    {
                        'month': '2026-05-01',
                        'visitors': 312,
                        'pageviews': 1_124,
                        'total_visits': 301,
                        'bounce_rate': 41.2,
                        'avg_duration_seconds': 198.7,
                        'views_per_visit': 3.73
                    }
                ],
                'message': 'Timeseries stats retrieved successfully.',
                'meta': {
                    'precision': 'month'
                }
            },
            response_only=True
        ),
        OpenApiExample(
            'Year precision example',
            value={
                'data': [
                    {
                        'year': '2026-01-01',
                        'visitors': 312,
                        'pageviews': 1_124,
                        'total_visits': 301,
                        'bounce_rate': 41.2,
                        'avg_duration_seconds': 198.7,
                        'views_per_visit': 3.73
                    }
                ],
                'message': 'Timeseries stats retrieved successfully.',
                'meta': {
                    'precision': 'year'
                }
            },
            response_only=True
        ),
    ]
)
class TimeseriesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        stats = {}
        granularity = None
        if date_arg.get('range'):
            # get granularity 
            granularity = self.auto_granularity(date_arg['range'])
            if granularity == 'day':
                stats = (StatsQueryService()
                         .get_daily_timeseries(site.id, 
                                               date_arg['range']['start'], 
                                               date_arg['range']['end']))
            elif granularity == 'month':
                stats = (StatsQueryService()
                         .get_monthly_timeseries(site.id, 
                                                 date_arg['range']['start'], 
                                                 date_arg['range']['end']))
            else:
                stats = (StatsQueryService()
                         .get_yearly_timeseries(site.id, 
                                                 date_arg['range']['start'], 
                                                 date_arg['range']['end']))
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_timeseries(site.id, date_arg['day'])
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_timeseries(site.id, start_dt=end, end_dt=now)
        else:
            stats = StatsQueryService().get_today_timeseries(site)

        return api_response(status.HTTP_200_OK, data=stats, meta={'precision': granularity or 'hour'})

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval:
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
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to day.",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        *PAGINATION_QUERY_PARAMETERS,
    ],
    summary="Get top pages viewed.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date. 
    Pass both start and end params for date ranges. 
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get top pages viewed.
""",
    responses={
        status.HTTP_200_OK: OpenApiResponse(response=TopPagesResponseSerializer()),
        **AUTH_RESPONSES,
    },
    examples=[
        OpenApiExample(
            'Top pages example',
            value={
                'data': [
                    {
                        'url': 'https://example.com/pricing',
                        'visitors': 54,
                        'pageviews': 168,
                    }
                ],
                'message': 'Top pages retrieved successfully.'
            },
            response_only=True
        ),
    ]
)
class TopPagesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_top_pages(site.id, date_arg['range']['start'], date_arg['range']['end'])
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_top_pages(site.id, date_arg['day'])
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_top_pages(site.id, start_dt=end, end_dt=now)
        else:
            stats = StatsQueryService().get_today_top_pages(site)

        # Extended view
        if 'offset' in request.query_params:
            paginator = AnalyticsPagination()
            page = paginator.paginate_queryset(stats, request, self)
            return paginator.get_paginated_response(page)
        else:
            # Shrunk view - default on dashboard
            limit = int(request.query_params.get('limit', 10))
            results = list(stats[:limit])
            return api_response(status.HTTP_200_OK, results)

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval:
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
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to day.",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        *PAGINATION_QUERY_PARAMETERS,
    ],
    summary="Get top referrers stats.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date. 
    Pass both start and end params for date ranges. 
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.    
    Get top referrers stats i.e source and medium e.g Organic search, Google.
    """,
    responses={
        status.HTTP_200_OK: OpenApiResponse(response=TopReferrersResponseSerializer()),
        **AUTH_RESPONSES,
    },
    examples=[
        OpenApiExample(
            'Top referrers example',
            value={
                'data': [
                    {
                        'source': 'google.com',
                        'medium': 'organic',
                        'visitors': 94,
                        'pageviews': 317,
                    }
                ],
                'message': 'Top referrers retrieved successfully.'
            },
            response_only=True
        ),
    ]
)
class TopReferrersView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_top_referrers(site.id, date_arg['range']['start'], date_arg['range']['end'])
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_top_referrers(site.id, date_arg['day'])
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_top_referrers(site.id, start_dt=end, end_dt=now)
        else:
            stats = StatsQueryService().get_today_top_referrers(site)

        # Extended view
        if 'offset' in request.query_params:
            paginator = AnalyticsPagination()
            page = paginator.paginate_queryset(stats, request, self)
            return paginator.get_paginated_response(page)
        else:
            # Shrunk view - default on dashboard
            limit = int(request.query_params.get('limit', 10))
            results = list(stats[:limit])
            return api_response(status.HTTP_200_OK, results)

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval:
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
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to day.",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        *PAGINATION_QUERY_PARAMETERS,
    ],
    summary="Get top countries stats.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges. 
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get countries visiting the site.
""",
    responses={
        status.HTTP_200_OK: OpenApiResponse(response=CountriesResponseSerializer()),
        **AUTH_RESPONSES,
    },
    examples=[
        OpenApiExample(
            'Top countries example',
            value={
                'data': [
                    {
                        'country': 'United States',
                        'visitors': 112,
                    }
                ],
                'message': 'Top countries retrieved successfully.'
            },
            response_only=True
        ),
    ]
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
            stats = StatsQueryService().get_today_country_breakdown(site)

        # Extended view
        if 'offset' in request.query_params:
            paginator = AnalyticsPagination()
            page = paginator.paginate_queryset(stats, request, self)
            return paginator.get_paginated_response(page)
        else:
            # Shrunk view - default on dashboard
            limit = int(request.query_params.get('limit', 10))
            results = list(stats[:limit])
            return api_response(status.HTTP_200_OK, results)

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval:
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
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to day.",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        *PAGINATION_QUERY_PARAMETERS,
    ],
    summary="Get device types.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges. 
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get devices used to visit the site.
""",
    responses={
        status.HTTP_200_OK: OpenApiResponse(response=DevicesResponseSerializer()),
        **AUTH_RESPONSES,
    },
    examples=[
        OpenApiExample(
            'Top devices example',
            value={
                'data': [
                    {
                        'device_type': 'Mobile',
                        'visitors': 183,
                    }
                ],
                'message': 'Device breakdown retrieved successfully.'
            },
            response_only=True
        ),
    ]
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
            stats = StatsQueryService().get_today_device_breakdown(site)

        # Extended view
        if 'offset' in request.query_params:
            paginator = AnalyticsPagination()
            page = paginator.paginate_queryset(stats, request, self)
            return paginator.get_paginated_response(page)
        else:
            # Shrunk view - default on dashboard
            limit = int(request.query_params.get('limit', 10))
            results = list(stats[:limit])
            return api_response(status.HTTP_200_OK, results)

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval:
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
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to day.",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        *PAGINATION_QUERY_PARAMETERS,
    ],
    summary="Get browsers stats.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges.
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get browsers used to visit the site.
""",
    responses={
        status.HTTP_200_OK: OpenApiResponse(response=BrowsersResponseSerializer()),
        **AUTH_RESPONSES,
    },
    examples=[
        OpenApiExample(
            'Top browsers example',
            value={
                'data': [
                    {
                        'browser': 'Chrome',
                        'visitors': 152,
                    }
                ],
                'message': 'Browser usage retrieved successfully.'
            },
            response_only=True
        ),
    ]
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
            stats = StatsQueryService().get_today_browser_breakdown(site)


        # Extended view
        if 'offset' in request.query_params:
            paginator = AnalyticsPagination()
            page = paginator.paginate_queryset(stats, request, self)
            return paginator.get_paginated_response(page)
        else:
            # Shrunk view - default on dashboard
            limit = int(request.query_params.get('limit', 10))
            results = list(stats[:limit])
            return api_response(status.HTTP_200_OK, results)

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval:
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
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to day.",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        *PAGINATION_QUERY_PARAMETERS,
    ],
    summary="Get operating system stats.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges.
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get operating systems used when visiting the site.
""",
    responses={
        status.HTTP_200_OK: OpenApiResponse(response=OSResponseSerializer()),
        **AUTH_RESPONSES,
    },
    examples=[
        OpenApiExample(
            'Top OS example',
            value={
                'data': [
                    {
                        'os': 'Android',
                        'visitors': 98,
                    }
                ],
                'message': 'Operating system breakdown retrieved successfully.'
            },
            response_only=True
        ),
    ]
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
            stats = StatsQueryService().get_today_os_breakdown(site)


        # Extended view
        if 'offset' in request.query_params:
            paginator = AnalyticsPagination()
            page = paginator.paginate_queryset(stats, request, self)
            return paginator.get_paginated_response(page)
        else:
            # Shrunk view - default on dashboard
            limit = int(request.query_params.get('limit', 10))
            results = list(stats[:limit])
            return api_response(status.HTTP_200_OK, results)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval:
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
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to day.",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        *PAGINATION_QUERY_PARAMETERS,
    ],
    summary="Get top regions.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges.
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get top regions visiting the site.
""",
    responses={
        status.HTTP_200_OK: OpenApiResponse(response=TopRegionsResponseSerializer()),
        **AUTH_RESPONSES,
    },
    examples=[
        OpenApiExample(
            'Top regions example',
            value={
                'data': [
                    {
                        'region': 'North America',
                        'visitors': 143,
                    }
                ],
                'message': 'Top regions retrieved successfully.'
            },
            response_only=True
        ),
    ]
)
class TopRegionsView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        date_arg = self.parse_date_range()
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_top_regions(site.id, date_arg['range']['start'], date_arg['range']['end'])
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_top_regions(site.id, date_arg['day'])
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_top_regions(site.id, start_dt=end, end_dt=now)
        else:
            stats = StatsQueryService().get_today_top_regions(site)

        # Extended view
        if 'offset' in request.query_params:
            paginator = AnalyticsPagination()
            page = paginator.paginate_queryset(stats, request, self)
            return paginator.get_paginated_response(page)
        else:
            # Shrunk view - default on dashboard
            limit = int(request.query_params.get('limit', 10))
            results = list(stats[:limit])
            return api_response(status.HTTP_200_OK, results)
        
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='interval',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="""Select the interval:
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
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to day.",
            required=False,
        ),
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        OpenApiParameter(
            name='end',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected. Only pass this if interval is set to custom.",
            required=False,
        ),
        *PAGINATION_QUERY_PARAMETERS,
    ],
    summary="Get top cities.",
    description="""Pass in a valid ISO 8601 format string as query params to start, end or day.
    Only pass in day param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges.
    Set interval as 24h to fetch stats for the past 24 hours.
    No query params defaults to today's stats.
    Get top cities visiting the site.
""",
    responses={
        status.HTTP_200_OK: OpenApiResponse(response=TopCitiesResponseSerializer()),
        **AUTH_RESPONSES,
    },
    examples=[
        OpenApiExample(
            'Top cities example',
            value={
                'data': [
                    {
                        'city': 'Lagos',
                        'visitors': 71,
                    }
                ],
                'message': 'Top cities retrieved successfully.'
            },
            response_only=True
        ),
    ]
)
class TopCitiesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(404, message='Site not found.')

        date_arg = self.parse_date_range()
        stats = {}
        if date_arg.get('range'):
            stats = StatsQueryService().get_top_cities(site.id, date_arg['range']['start'], date_arg['range']['end'])
        elif date_arg.get('day'):
            stats = StatsQueryService().get_anyday_top_cities(site.id, date_arg['day'])
        elif date_arg.get('hour'):
            now = timezone.now()
            end = now - timedelta(hours=24)
            stats = StatsQueryService().get_hourly_top_cities(site.id, start_dt=end, end_dt=now)
        else:
            stats = StatsQueryService().get_today_top_cities(site)

        # Extended view
        if 'offset' in request.query_params:
            paginator = AnalyticsPagination()
            page = paginator.paginate_queryset(stats, request, self)
            return paginator.get_paginated_response(page)
        else:
            # Shrunk view - default on dashboard
            limit = int(request.query_params.get('limit', 10))
            results = list(stats[:limit])
            return api_response(status.HTTP_200_OK, results)