from rest_framework import serializers
from .models import Site
from common.validators import validate_domain
from common.utils import _get_zoneinfo

class CreateSiteSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=255)
    timezone = serializers.CharField(max_length=50,
                                     default='UTC',
                                     required=False,
                                     help_text='IANA timezone name (e.g. Europe/London). Defaults to UTC.')

    def validate_domain(self, value):
        return validate_domain(value)
    
    def validate_timezone(self, value):
        try:
            _get_zoneinfo(value)
        except ValueError as e:
            raise serializers.ValidationError(
                f"Unknown timezone: {value}"
            )
        return value

class UpdateSiteSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=255, required=False)
    timezone = serializers.CharField(max_length=50,
                                     default='UTC',
                                     required=False,
                                     help_text='IANA timezone name (e.g. Europe/London). Defaults to UTC.')

    def validate_domain(self, value):
        return validate_domain(value)
    
    def validate_timezone(self, value):
        try:
            _get_zoneinfo(value)
        except ValueError as e:
            raise serializers.ValidationError(
                f"Unknown timezone: {value}"
            )
        return value


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ['public_id', 'domain', 'tracking_token', 'timezone', 'is_active', 'created_at']
        read_only_fields = fields