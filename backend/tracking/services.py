from user_agents import parse as ua_parse
from .models import Event
from .geo import geolocate
from .referrer import parse_referrer
from datetime import date

class IngestionService:
    """Handles the recording of a single pageview event."""

    def record_event(self, site_id: int, payload: dict, ip_address: str = None,
                     user_agent_str: str = None) -> Event:
        ua = ua_parse(user_agent_str or '')
        location = geolocate(ip_address) if ip_address else {}

        source, medium = parse_referrer(payload.get('referrer', ''))

        event = Event.objects.create(
            site_id=site_id,
            visitor_id=payload['visitor_id'],
            url=payload['url'],
            referrer=payload.get('referrer'),
            timezone=payload.get('timezone'),
            source=source,
            medium=medium,
            browser=ua.browser.family,
            os=ua.os.family,
            device_type=self._device_type(ua),
            user_agent=user_agent_str,
            ip_address=ip_address,
            country=location.get('country', ''),
            region=location.get('region', ''),
            city=location.get('city', ''),
        )
        return event

    @staticmethod
    def _device_type(ua):
        if ua.is_mobile:
            return 'mobile'
        elif ua.is_tablet:
            return 'tablet'
        return 'desktop'
    
class EventService:
    
    def get_site_events(self, site_id: int, day: date):
        """Get all events for a site on a given day"""
        return Event.objects.filter(site_id=site_id, timestamp__date=day)

    def get_site_events_date_range(self, site_id: int, start: date, end: date):
        """Get all events for a site for a given start and end date range"""
        return Event.objects.filter(
            site_id=site_id,
            timestamp__date__gte=start,
            timestamp__date__lte=end
        )