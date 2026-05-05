import time
from .metrics import request_count, request_latency

class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration = time.time() - start
        # Get the view name or a placeholder
        endpoint = request.resolver_match.view_name if request.resolver_match else 'unknown'
        request_count.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        request_latency.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        return response