from prometheus_client import Counter, Histogram

# HTTP metrics
request_count = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)
request_latency = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

# Email metrics
email_sent_total = Counter(
    'email_sent_total',
    'Total emails sent',
    ['type', 'status']
)
email_retries_total = Counter(
    'email_retries_total',
    'Total number of retry attempts'
)