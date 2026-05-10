from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

class CorsMiddleware(MiddlewareMixin):
    def process_response(self, request, response):

        if request.path.startswith('/api/event'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Credentials'] = 'false'
            response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, X-Tracking-Token'
            response['Access-Control-Max-Age'] = '86400'
            return response

        allowed_origins = getattr(
            settings, 'CORS_ALLOWED_ORIGINS', ['http://localhost:3000']
        )
        origin = request.headers.get('Origin')

        # If the request has an Origin header and it's allowed, set the headers
        if origin and origin in allowed_origins:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
        elif origin and '*' in allowed_origins:
            response['Access-Control-Allow-Origin'] = '*'

        response['Access-Control-Allow-Methods'] = getattr(
            settings,
            'CORS_ALLOWED_METHODS',
            'GET, POST, PUT, PATCH, DELETE, OPTIONS',
        )
        response['Access-Control-Allow-Headers'] = getattr(
            settings,
            'CORS_ALLOWED_HEADERS',
            'Authorization, Content-Type, X-CSRFToken, X-Correlation-ID, X-Tracking-Token',
        )
        response['Access-Control-Max-Age'] = getattr(
            settings, 'CORS_MAX_AGE', 86400   # 24 hours
        )

        return response
