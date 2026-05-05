from django.http import HttpResponse
from prometheus_client import generate_latest

def metrics_view(request):
    return HttpResponse(generate_latest(), content_type='text/plain; version=0.0.4')