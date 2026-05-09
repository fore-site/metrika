from django.urls import path
from .views import SiteListCreateView, SiteDetailView

urlpatterns = [
    path('', SiteListCreateView.as_view(), name='site-list'),
    path('<uuid:public_id>/', SiteDetailView.as_view(), name='site-detail'),
]