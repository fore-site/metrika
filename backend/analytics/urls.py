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
]