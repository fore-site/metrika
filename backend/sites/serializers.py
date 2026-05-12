from rest_framework import serializers
from .models import Site
from common.validators import validate_domain

class CreateSiteSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=255)

    def validate_domain(self, value):
        return validate_domain(value)

class UpdateSiteSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=255, required=False)

    def validate_domain(self, value):
        return validate_domain(value)


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ['public_id', 'domain', 'tracking_token', 'is_active', 'created_at']
        read_only_fields = ['tracking_token', 'created_at']