from django.urls import path
from .views import (
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
    trigger_aggregation,
)

from .demo_views import (
    DemoTimeseriesView,
    DemoSummaryView,
    DemoTopPagesView,
    DemoTopReferrersView,
    DemoCountriesView,
    DemoDevicesView,
    DemoBrowsersView,
    DemoOSView,
    DemoTopRegionsView,
    DemoTopCitiesView,
)


urlpatterns = [
    path('<int:site_id>/summary/', SummaryView.as_view(), name='summary'),
    path('<int:site_id>/timeseries/', TimeseriesView.as_view(), name='timeseries'),
    path('<int:site_id>/top-pages/', TopPagesView.as_view(), name='top-pages'),
    path('<int:site_id>/top-referrers/', TopReferrersView.as_view(), name='top-referrers'),
    path('<int:site_id>/countries/', CountriesView.as_view(), name='countries'),
    path('<int:site_id>/devices/', DevicesView.as_view(), name='devices'),
    path('<int:site_id>/browsers/', BrowsersView.as_view(), name='browsers'),
    path('<int:site_id>/os/', OSView.as_view(), name='os'),
    path('<int:site_id>/top-regions/', TopRegionsView.as_view(), name='top-regions'),
    path('<int:site_id>/top-cities/', TopCitiesView.as_view(), name='top-cities'),

    # Public demo routes – ignore the site_id parameter
    path('demo/<int:site_id>/summary/', DemoSummaryView.as_view(), name='demo-summary'),
    path('demo/<int:site_id>/timeseries/', DemoTimeseriesView.as_view(), name='demo-timeseries'),
    path('demo/<int:site_id>/top-pages/', DemoTopPagesView.as_view(), name='demo-top-pages'),
    path('demo/<int:site_id>/top-referrers/', DemoTopReferrersView.as_view(), name='demo-top-referrers'),
    path('demo/<int:site_id>/countries/', DemoCountriesView.as_view(), name='demo-countries'),
    path('demo/<int:site_id>/devices/', DemoDevicesView.as_view(), name='demo-devices'),
    path('demo/<int:site_id>/browsers/', DemoBrowsersView.as_view(), name='demo-browsers'),
    path('demo/<int:site_id>/os/', DemoOSView.as_view(), name='demo-os'),
    path('demo/<int:site_id>/top-regions/', DemoTopRegionsView.as_view(), name='demo-top-regions'),
    path('demo/<int:site_id>/top-cities/', DemoTopCitiesView.as_view(), name='demo-top-cities'),

    path('internal/aggregate/', trigger_aggregation, name='trigger-aggregation'),
]