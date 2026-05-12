from datetime import date
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from common.response import api_response
from sites.services import SiteService
from .services import StatsQueryService
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from common.openapi import envelope_success



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
        """Extract start/end dates from query params; default to last 30 days."""
        end = None
        start = date.today()
        try:
            if 'start' in self.request.query_params:
                start = date.fromisoformat(self.request.query_params['start'])
            if 'end' in self.request.query_params:
                end = date.fromisoformat(self.request.query_params['end'])
        except ValueError as e:
            raise ValueError(str(e))
        return start, end

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
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=True,
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
    description="""Pass in a valid ISO 8601 format string as query params to start or end.
    Only pass in start param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges.
    Get summary stats.""",
    responses=envelope_success,
)
class SummaryView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        start, end = self.parse_date_range()
        stats = {}
        if start != date.today() and end:
            stats = StatsQueryService().get_site_summary(site.id, start, end)
        if start != date.today() and not end:
            stats = StatsQueryService().get_anyday_site_summary(site.id, start)
        if start == date.today() and not end:
            stats = StatsQueryService().get_today_site_summary(site.id)
        
        return api_response(status.HTTP_200_OK, data=stats)

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=True,
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
    description="""Pass in a valid ISO 8601 format string as query params to start or end. 
    Get timeseries stats for visualization (graph plotting, etc).
    Only pass in start param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges""",
    responses=envelope_success,
)
class TimeseriesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        start, end = self.parse_date_range()
        stats = {}
        if start != date.today() and end:
            stats = StatsQueryService().get_timeseries(site.id, start, end)
        if start != date.today() and not end:
            stats = StatsQueryService().get_anyday_timeseries(site.id, start)
        if start == date.today() and not end:
            stats = StatsQueryService().get_today_timeseries(site.id)

        return api_response(status.HTTP_200_OK, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=True,
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
    description="""Pass in a valid ISO 8601 format string as query params to start or end. 
    Get top pages viewed.
    Only pass in start param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges""",
    responses=envelope_success,
)
class TopPagesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        start, end = self.parse_date_range()
        limit = self.get_limit(10)
        stats = {}
        if start != date.today() and end:
            stats = StatsQueryService().get_top_pages(site.id, start, end, limit)
        if start != date.today() and not end:
            stats = StatsQueryService().get_anyday_top_pages(site.id, start, limit)
        if start == date.today() and not end:
            stats = StatsQueryService().get_today_top_pages(site.id, limit)

        return api_response(status.HTTP_200_OK, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=True,
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
    description="""Pass in a valid ISO 8601 format string as query params to start or end. 
    Get top referrers stats i.e source and medium e.g Organic search, Google.
    Only pass in start param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges""",
    responses=envelope_success,
)
class TopReferrersView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        start, end = self.parse_date_range()
        limit = self.get_limit(10)
        stats = {}
        if start != date.today() and end:
            stats = StatsQueryService().get_top_referrers(site.id, start, end, limit)
        if start != date.today() and not end:
            stats = StatsQueryService().get_anyday_top_referrers(site.id, start, limit)
        if start == date.today() and not end:
            stats = StatsQueryService().get_today_top_referrers(site.id, limit)

        return api_response(status.HTTP_200_OK, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=True,
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
    description="""Pass in a valid ISO 8601 format string as query params to start or end. 
    Get countries visiting the site.
    Only pass in start param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges""",
    responses=envelope_success,
)
class CountriesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        start, end = self.parse_date_range()
        stats = {}
        if start != date.today() and end:
            stats = StatsQueryService().get_country_breakdown(site.id, start, end)
        if start != date.today() and not end:
            stats = StatsQueryService().get_anyday_country_breakdown(site.id, start)
        if start == date.today() and not end:
            stats = StatsQueryService().get_today_country_breakdown(site.id)

        return api_response(status.HTTP_200_OK, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=True,
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
    description="""Pass in a valid ISO 8601 format string as query params to start or end. 
    Get devices used to visit the site.
    Only pass in start param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges""",
    responses=envelope_success,
)
class DevicesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        start, end = self.parse_date_range()
        stats = {}
        if start != date.today() and end:
            stats = StatsQueryService().get_device_breakdown(site.id, start, end)
        if start != date.today() and not end:
            stats = StatsQueryService().get_anyday_device_breakdown(site.id, start)
        if start == date.today() and not end:
            stats = StatsQueryService().get_today_device_breakdown(site.id)

        return api_response(status.HTTP_200_OK, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=True,
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
    description="""Pass in a valid ISO 8601 format string as query params to start or end. 
    Get browsers used to visit the site.
    Only pass in start param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges""",
    responses=envelope_success,
)
class BrowsersView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        start, end = self.parse_date_range()
        stats = {}
        if start != date.today() and end:
            stats = StatsQueryService().get_browser_breakdown(site.id, start, end)
        if start != date.today() and not end:
            stats = StatsQueryService().get_anyday_browser_breakdown(site.id, start)
        if start == date.today() and not end:
            stats = StatsQueryService().get_today_browser_breakdown(site.id)

        return api_response(status.HTTP_200_OK, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=True,
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
    description="""Pass in a valid ISO 8601 format string as query params to start or end. 
    Get operating systems used when visiting the site.
    Only pass in start param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges""",
    responses=envelope_success,
)
class OSView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        start, end = self.parse_date_range()
        stats = {}
        if start != date.today() and end:
            stats = StatsQueryService().get_os_breakdown(site.id, start, end)
        if start != date.today() and not end:
            stats = StatsQueryService().get_anyday_os_breakdown(site.id, start)
        if start == date.today() and not end:
            stats = StatsQueryService().get_today_os_breakdown(site.id)

        return api_response(status.HTTP_200_OK, data=list(stats))


# On‑demand endpoints (from raw Event table)

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=True,
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
    description="""Pass in a valid ISO 8601 format string as query params to start or end. 
    Get top regions visiting the site.
    Only pass in start param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges""",
    responses=envelope_success,
)
class TopRegionsView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        start, end = self.parse_date_range()
        limit = self.get_limit(10)
        stats = {}
        if start != date.today() and end:
            stats = StatsQueryService().get_top_regions(site.id, start, end, limit)
        if start != date.today() and not end:
            stats = StatsQueryService().get_anyday_top_regions(site.id, start, limit)
        if start == date.today() and not end:
            stats = StatsQueryService().get_today_top_regions(site.id, limit)

        return api_response(200, data=list(stats))

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='start',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Pass in a date string in the format YYYY-MM-DD. Any other format is rejected",
            required=True,
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
    description="""Pass in a valid ISO 8601 format string as query params to start or end. 
    Get top cities visiting the site.
    Only pass in start param if you need to fetch stats for a specific date.
    Pass both start and end params for date ranges""",
    responses=envelope_success,
)
class TopCitiesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(404, message='Site not found.')

        start, end = self.parse_date_range()
        limit = self.get_limit(10)
        stats = {}
        if start != date.today() and end:
            stats = StatsQueryService().get_top_cities(site.id, start, end, limit)
        if start != date.today() and not end:
            stats = StatsQueryService().get_anyday_top_cities(site.id, start, limit)
        if start == date.today() and not end:
            stats = StatsQueryService().get_today_top_cities(site.id, limit)

        return api_response(200, data=list(stats))