from .settings import *

DATABASES = {
    'default': dj_database_url.config(ssl_require=False)
}

# Redis from environment
RQ_QUEUES = {
    'default': {
        'URL': config('REDIS_URL', default='redis://localhost:6379/0'),
    }
}

# Disable throttling during tests
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []