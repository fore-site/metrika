from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from common.response import api_response
from sites.services import SiteService
from .services import StatsQueryService


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
        end = date.today()
        start = end - timedelta(days=30)
        if 'start' in self.request.query_params:
            start = date.fromisoformat(self.request.query_params['start'])
        if 'end' in self.request.query_params:
            end = date.fromisoformat(self.request.query_params['end'])
        return start, end

    def get_limit(self, default=10):
        """Extract limit from query params, clamped to 1-100."""
        try:
            limit = int(self.request.query_params.get('limit', default))
            return max(1, min(limit, 100))
        except (ValueError, TypeError):
            return default


# ----------------------------------------------------------------------
# Aggregated endpoints (fast, from daily summary tables)
# ----------------------------------------------------------------------
class SummaryView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(404, message='Site not found.')

        start, end = self.parse_date_range()
        stats = StatsQueryService().get_site_summary(site.id, start, end)
        return api_response(200, data=stats)


class TimeseriesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(404, message='Site not found.')

        start, end = self.parse_date_range()
        data = StatsQueryService().get_timeseries(site.id, start, end)
        return api_response(200, data=list(data))


class TopPagesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(404, message='Site not found.')

        start, end = self.parse_date_range()
        limit = self.get_limit(10)
        data = StatsQueryService().get_top_pages(site.id, start, end, limit)
        return api_response(200, data=list(data))


class TopReferrersView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(404, message='Site not found.')

        start, end = self.parse_date_range()
        limit = self.get_limit(10)
        data = StatsQueryService().get_top_referrers(site.id, start, end, limit)
        return api_response(200, data=list(data))


class CountriesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(404, message='Site not found.')

        start, end = self.parse_date_range()
        data = StatsQueryService().get_country_breakdown(site.id, start, end)
        return api_response(200, data=list(data))


class DevicesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(404, message='Site not found.')

        start, end = self.parse_date_range()
        data = StatsQueryService().get_device_breakdown(site.id, start, end)
        return api_response(200, data=list(data))


class BrowsersView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(404, message='Site not found.')

        start, end = self.parse_date_range()
        data = StatsQueryService().get_browser_breakdown(site.id, start, end)
        return api_response(200, data=list(data))


class OSView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(404, message='Site not found.')

        start, end = self.parse_date_range()
        data = StatsQueryService().get_os_breakdown(site.id, start, end)
        return api_response(200, data=list(data))


# ----------------------------------------------------------------------
# On‑demand endpoints (from raw Event table)
# ----------------------------------------------------------------------
class TopRegionsView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(404, message='Site not found.')

        start, end = self.parse_date_range()
        limit = self.get_limit(10)
        data = StatsQueryService().get_top_regions(site.id, start, end, limit)
        return api_response(200, data=list(data))


class TopCitiesView(BaseStatsView):
    def get(self, request, site_id):
        site = self.get_site(site_id)
        if not site:
            return api_response(404, message='Site not found.')

        start, end = self.parse_date_range()
        limit = self.get_limit(10)
        data = StatsQueryService().get_top_cities(site.id, start, end, limit)
        return api_response(200, data=list(data))