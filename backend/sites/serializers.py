# sites/serializers.py
from rest_framework import serializers
from .models import Site

class CreateSiteSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=255)

    def validate_domain(self, value):
        value = value.lower().strip().rstrip('/')
        if not value:
            raise serializers.ValidationError('Domain cannot be empty.')
        # Optionally, reject invalid characters, but keep simple for now.
        return value

class UpdateSiteSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=255, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_domain(self, value):
        if value:
            value = value.lower().strip().rstrip('/')
        return value

class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ['id', 'domain', 'tracking_token', 'is_active', 'created_at']
        read_only_fields = ['id', 'tracking_token', 'created_at']# sites/serializers.py
from rest_framework import serializers
from .models import Site

class CreateSiteSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=255)

    def validate_domain(self, value):
        value = value.lower().strip().rstrip('/')
        if not value:
            raise serializers.ValidationError('Domain cannot be empty.')
        # Optionally, reject invalid characters, but keep simple for now.
        return value

class UpdateSiteSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=255, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_domain(self, value):
        if value:
            value = value.lower().strip().rstrip('/')
        return value

class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ['id', 'domain', 'tracking_token', 'is_active', 'created_at']
        read_only_fields = ['id', 'tracking_token', 'created_at']