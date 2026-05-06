from rest_framework.response import Response

def api_response(status_code: int, data=None, message: str = '', errors=None) -> Response:
    """Build a consistent JSON envelope."""
    is_success = 200 <= status_code < 300
    body = {
        'message': message or default_message(status_code),
    }

    if is_success:
        body['data'] = data if data is not None else {}
    else:
        body['errors'] = errors or []

    return Response(body, status=status_code)

def default_message(status_code: int) -> str:
    return {
        200: 'Request successful.',
        201: 'Resource created successfully.',
        204: 'No content.',
        400: 'The request was invalid.',
        401: 'Authentication credentials were not provided or are invalid.',
        403: 'You do not have permission to perform this action.',
        404: 'The requested resource was not found.',
        500: 'An unexpected error occurred. Please try again later.',
    }.get(status_code, '')