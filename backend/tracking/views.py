from rest_framework import status
from rest_framework.views import APIView
from common.response import api_response
from sites.services import SiteService
from .services import IngestionService
from .serializers import EventPayloadSerializer
from common.utils import get_client_ip, get_user_agent
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

@extend_schema(
    summary="Send event payload",
    parameters=[
        OpenApiParameter(
            name='X-Tracking-Token',
            type=str,
            location=OpenApiParameter.HEADER,
            description="The tracking token of a user's site.",
            required=True,
        )
    ],
    description="Send event payload for each page view along with X-Tracking-Token header",
    request=EventPayloadSerializer,
    responses={status.HTTP_204_NO_CONTENT: OpenApiResponse(
        description='Event recorded successfully',
        response=None
    )},
)
class EventView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        token = request.headers.get('X-Tracking-Token')
        if not token:
            return api_response(status.HTTP_401_UNAUTHORIZED, message='Missing tracking token.')

        site = SiteService().get_site_by_token(token)
        if not site:
            return api_response(status.HTTP_401_UNAUTHORIZED, message='Invalid tracking token.')

        # Validate payload
        serializer = EventPayloadSerializer(data=request.data, context={'site': site})
        serializer.is_valid(raise_exception=True)

        ip = get_client_ip(request)
        ua = get_user_agent(request)

        # Record event
        IngestionService().record_event(
            site_id=site.id,
            payload=serializer.validated_data,
            ip_address=ip,
            user_agent_str=ua,
        )

        return api_response(status.HTTP_204_NO_CONTENT)