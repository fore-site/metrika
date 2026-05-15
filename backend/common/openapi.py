from drf_spectacular.utils import inline_serializer
from rest_framework import serializers
from drf_spectacular.openapi import AutoSchema


error_object = inline_serializer(
    name='ErrorObject',
    fields={
        'code': serializers.CharField(),
        'detail': serializers.CharField(),
        'source': inline_serializer(
            name='ErrorSource',
            fields={'pointer': serializers.CharField()},
            source=None,
        ),
    },
    source=None,
)

envelope_error = inline_serializer(
    name='ErrorEnvelope',
    fields={
        'message': serializers.CharField(),
        'errors': serializers.ListField(child=error_object),
    },
    source=None,
)

# Single reusable success envelope – data is generic DictField
# envelope_success = inline_serializer(
#     name='SuccessEnvelope',
#     fields={
#         'data': serializers.DictField(),
#         'message': serializers.CharField(default='This is a success response.'),
#     },
#     source=None,
# )


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
            responses['401'] = envelope_error
        if '403' not in responses:
            responses['403'] = envelope_error
        if '500' not in responses:
            responses['500'] = envelope_error
        return responses