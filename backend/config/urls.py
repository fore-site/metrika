from django.urls import path, include
from common.views import metrics_view
from drf_spectacular.views import SpectacularSwaggerView

urlpatterns = [
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('metrics/', metrics_view, name='metrics'),
    path('api/auth/', include('accounts.urls')),
    path('api/sites/', include('sites.urls')),
    path('api/stats/', include('analytics.urls')),
    path('api/events/', include('tracking.urls')),
]
