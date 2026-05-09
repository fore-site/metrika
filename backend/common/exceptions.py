from rest_framework.views import exception_handler
from .response import api_response
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    # Get a standard error response
    response = exception_handler(exc, context)

    if response is not None:
        status_code = response.status_code
        drf_data = response.data

        message = ''
        errors = []

        if isinstance(drf_data, dict):
            # Check for a simple 'detail' key (like 401 Unauthorized)
            if 'detail' in drf_data and len(drf_data) == 1:
                message = str(drf_data['detail'])
            else:
                # Field‑level validation errors: convert to error objects
                for field, field_errors in drf_data.items():
                    if isinstance(field_errors, list):
                        for error in field_errors:
                            errors.append({
                                'code': 'invalid',
                                'detail': str(error),
                                'source': {'pointer': f'/{field}'},
                            })
                    else:
                        errors.append({
                            'code': 'invalid',
                            'detail': field_errors,
                            'source': {'pointer': f'/{field}'},
                        })
                message = 'Validation error.'
        elif isinstance(drf_data, list):
            message = str(drf_data[0]) if drf_data else ''
            errors.append({
                'code': 'invalid',
                'detail': message,
            })

        return api_response(
            status_code=status_code,
            data=None,
            message=message,
            errors=errors if errors else None,
        )

    # For unhandled exceptions, return a generic 500 envelope
    logger.error(f"Unhandled error: {exc}")
    return api_response(500, message='An unexpected error occurred.')