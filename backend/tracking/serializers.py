from rest_framework import serializers

class EventPayloadSerializer(serializers.Serializer):
    visitor_id = serializers.CharField(max_length=64)
    url = serializers.URLField(max_length=2048)
    referrer = serializers.URLField(max_length=2048, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=64, required=False, allow_blank=True)
    # Optionally validate that url starts with "/" or is full? We'll accept any valid URL.