from drf_spectacular.utils import inline_serializer
from drf_spectacular.openapi import AutoSchema
from rest_framework import serializers

# Error components

error_source = inline_serializer(
    name='ErrorSource',
    fields={'pointer': serializers.CharField()},
    source=None,
)

error_object = inline_serializer(
    name='ErrorObject',
    fields={
        'code': serializers.CharField(),
        'detail': serializers.CharField(),
        'source': error_source,
    },
    source=None,
)

# Envelope functions

def envelope_success(data_serializer=None, description='Success response'):
    props = {
        'data': data_serializer if data_serializer else serializers.DictField(default={}),
        'message': serializers.CharField(default=''),
    }
    return inline_serializer(name='SuccessEnvelope', fields=props, source=None)

def envelope_error():
    return inline_serializer(
        name='ErrorEnvelope',
        fields={
            'message': serializers.CharField(),
            'errors': serializers.ListField(child=error_object),
        },
        source=None,
    )


class EnvelopeAutoSchema(AutoSchema):
    """
    Automatically adds standard error responses (401, 403, 500) to every endpoint.
    """
    def get_override_responses(self):
        responses = super().get_override_responses()
        if not responses:
            responses = {}
        # Only add if not already defined
        if '401' not in responses:
            responses['401'] = envelope_error()
        if '403' not in responses:
            responses['403'] = envelope_error()
        if '500' not in responses:
            responses['500'] = envelope_error()
        return responses