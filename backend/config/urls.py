from django.urls import path, include

urlpatterns = [
    path('api/auth/', include('accounts.urls')),
    path('api/sites/', include('sites.urls')),
    path('api/stats/', include('analytics.urls')),
    path('api/events/', include('tracking.urls')),
]
