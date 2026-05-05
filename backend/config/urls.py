from django.urls import path, include
from common.views import metrics_view

urlpatterns = [
    path('metrics/', metrics_view, name='metrics'),
    path('api/auth/', include('accounts.urls')),
    path('api/sites/', include('sites.urls')),
    path('api/stats/', include('analytics.urls')),
    path('api/events/', include('tracking.urls')),
]
