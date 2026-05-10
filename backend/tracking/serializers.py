from rest_framework import serializers
from urllib.parse import urlparse

class EventPayloadSerializer(serializers.Serializer):
    visitor_id = serializers.UUIDField()
    url = serializers.URLField(max_length=2048)
    referrer = serializers.URLField(max_length=2048, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=64, required=False, allow_blank=True)

    def validate_url(self, value):
        site = self.context.get('site')
        if not site:
            raise serializers.ValidationError("Site context missing. Cannot verify domain")
        domain = site.domain
        hostname = urlparse(value).hostname or ''
        if hostname != domain and not hostname.endswith('.' + domain):
            raise serializers.ValidationError("URL domain does not match the registered tracking site.")
        return value