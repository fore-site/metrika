from django.http import HttpResponse, JsonResponse
from prometheus_client import generate_latest
from django.db import connections
from redis import Redis
from django.conf import settings
from django.shortcuts import render
from prometheus_client import REGISTRY
from django.views.decorators.http import require_GET

@require_GET
def metrics_view(request):
    return HttpResponse(generate_latest(), content_type='text/plain; version=0.0.4')

@require_GET
def health_check(request):
    status_code = 200
    health = {
        'status': 'healthy',
        'database': 'ok',
        'redis': 'ok',
    }

    # Check database
    try:
        connections['default'].cursor()
    except Exception:
        health['database'] = 'unavailable'
        health['status'] = 'unhealthy'
        status_code = 503

    # Check Redis
    try:
        redis_url = settings.RQ_QUEUES['default'].get('URL')
        if redis_url:
            r = Redis.from_url(redis_url)
            r.ping()
    except Exception:
        health['redis'] = 'unavailable'
        health['status'] = 'degraded' if health['status'] == 'healthy' else 'unhealthy'

    return JsonResponse(health, status=status_code)

@require_GET
def metrics_dashboard(request):
    """Human‑readable metrics page."""
    metrics = []
    for metric in REGISTRY.collect():
        for sample in metric.samples:
            metrics.append({
                'name': sample.name,
                'labels': sample.labels,
                'value': sample.value,
                'type': metric.type,
                'help': metric.documentation,
            })

    context = {
        'metrics': metrics,
        'count': len(metrics),
    }
    return render(request, 'common/metrics_dashboard.html', context)