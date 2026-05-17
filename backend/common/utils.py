from ipware import get_client_ip as _get_client_ip
from datetime import date, datetime, timedelta, timezone as dt_timezone
from functools import lru_cache
from zoneinfo import ZoneInfo, available_timezones


def get_client_ip(request):
        """Extract real client IP, even behind proxies."""
        ip, _ = _get_client_ip(request)
        if ip is None:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

def get_user_agent(request):
        """Extract user agent string."""
        return request.META.get('HTTP_USER_AGENT', '')


@lru_cache(maxsize=256)
def _get_zoneinfo(tz_name: str) -> ZoneInfo:
    """Cached ZoneInfo lookup."""
    if tz_name not in available_timezones():
        raise ValueError(f"Unknown timezone: {tz_name}")
    return ZoneInfo(tz_name)

def get_site_timezone(site):
    """Return a ZoneInfo instance for the site's configured timezone."""
    return _get_zoneinfo(site.timezone)

def get_local_day_utc_range(site, local_date: date):
    """
    Given a site and a date in its local time,
    return (start_utc, end_utc) as UTC datetimes covering exactly that day.
    """
    tz = get_site_timezone(site)

    # Midnight in local time – using the constructor avoids DST ambiguity
    start_local = datetime(local_date.year, local_date.month, local_date.day,
                           tzinfo=tz)
    # Midnight of the next day
    next_day = local_date + timedelta(days=1)
    end_local = datetime(next_day.year, next_day.month, next_day.day,
                         tzinfo=tz)

    start_utc = start_local.astimezone(dt_timezone.utc)
    end_utc = end_local.astimezone(dt_timezone.utc)
    return start_utc, end_utc