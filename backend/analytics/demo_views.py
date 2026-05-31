from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.permissions import AllowAny
from sites.models import Site
from .views import (
    BaseStatsView,
    SummaryView,
    TimeseriesView,
    TopPagesView,
    TopReferrersView,
    CountriesView,
    DevicesView,
    BrowsersView,
    OSView,
    TopRegionsView,
    TopCitiesView,
)
import logging

logger = logging.getLogger(__name__)


class DemoBaseStatsView(BaseStatsView):
    """
    Overrides get_site to always return the demo site, bypassing ownership checks.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'demo'

    def get_site(self, site_id=None):
        """Return the demo site, ignoring the provided site_id."""
        site_id = getattr(settings, 'DEMO_SITE_ID', None)
        if not site_id:
            raise ImproperlyConfigured('DEMO_SITE_ID is not set in settings.')
        try:
            return Site.objects.get(id=site_id, is_active=True)
        except Site.DoesNotExist:
            logger.info(f'Site with id {site_id} does not exist')
            return None


# Now create public versions of each analytics view
class DemoTimeseriesView(DemoBaseStatsView, TimeseriesView):
    pass

class DemoSummaryView(DemoBaseStatsView, SummaryView):
    pass

class DemoTopPagesView(DemoBaseStatsView, TopPagesView):
    pass

class DemoTopReferrersView(DemoBaseStatsView, TopReferrersView):
    pass

class DemoCountriesView(DemoBaseStatsView, CountriesView):
    pass

class DemoDevicesView(DemoBaseStatsView, DevicesView):
    pass

class DemoBrowsersView(DemoBaseStatsView, BrowsersView):
    pass

class DemoOSView(DemoBaseStatsView, OSView):
    pass

class DemoTopRegionsView(DemoBaseStatsView, TopRegionsView):
    pass

class DemoTopCitiesView(DemoBaseStatsView, TopCitiesView):
    pass