from django.urls import path, include
from common.views import metrics_view, health_check, metrics_dashboard
from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('metrics/', metrics_view, name='metrics'),
    path('metrics/dashboard/', metrics_dashboard, name='metrics-dashboard'),  # Human readable
    path('health/', health_check, name='health'),
    path('api/auth/', include('accounts.urls')),
    path('api/sites/', include('sites.urls')),
    path('api/stats/', include('analytics.urls')),
    path('api/events/', include('tracking.urls')),
]
