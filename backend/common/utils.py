from ipware import get_client_ip as _get_client_ip
def get_client_ip(request):
        """Extract real client IP, even behind proxies."""
        ip, _ = _get_client_ip(request)
        if ip is None:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

def get_user_agent(request):
        """Extract user agent string."""
        return request.META.get('HTTP_USER_AGENT', '')