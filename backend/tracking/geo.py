import logging
from django.contrib.gis.geoip2 import GeoIP2, GeoIP2Exception

logger = logging.getLogger(__name__)

g = GeoIP2()

def geolocate(ip_address: str) -> dict:
    """
    Return {'country': ..., 'region': ..., 'city': ...} for the given IP.
    Returns empty dict if IP is private, not found, or an error occurs.
    """
    if not ip_address or ip_address.startswith(('127.', '10.', '192.168.', '172.16.')):
        return {}
    try:
        response = g.city(ip_address)
        return {
            'continent': response.get('continent_name', ''),
            'country': response.get('country_name', ''),
            'region':  response.get('region_name', ''),
            'city':    response.get('city', ''),
        }
    except (GeoIP2Exception, ValueError) as e:
        logger.debug(f'GeoIP lookup failed for {ip_address}: {e}')
        return {}