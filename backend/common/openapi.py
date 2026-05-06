from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

# ---- Error components ----

error_source = inline_serializer(
    name='ErrorSource',
    fields={'pointer': serializers.CharField()},
    source=None,           # ← explicit
)

error_object = inline_serializer(
    name='ErrorObject',
    fields={
        'code': serializers.CharField(),
        'detail': serializers.CharField(),
        'source': error_source,          # note: field name 'source', not DRF source argument
    },
    source=None,           # ← fix for the assertion
)

# ---- Envelope functions ----

def envelope_success(data_serializer=None, description='Success response'):
    props = {
        'status': serializers.CharField(default='success'),
        'data': data_serializer if data_serializer else serializers.DictField(default={}),
        'message': serializers.CharField(default=''),
    }
    return inline_serializer(name='SuccessEnvelope', fields=props, source=None)

def envelope_error():
    return inline_serializer(
        name='ErrorEnvelope',
        fields={
            'status': serializers.CharField(default='error'),
            'message': serializers.CharField(),
            'errors': serializers.ListField(child=error_object),
        },
        source=None,
    )