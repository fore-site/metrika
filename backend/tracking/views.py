from rest_framework import status
from rest_framework.views import APIView
from common.response import api_response
from sites.services import SiteService
from .services import IngestionService
from .serializers import EventPayloadSerializer
from .utils import get_client_ip, get_user_agent

class EventView(APIView):
    permission_classes = []   # public
    authentication_classes = []

    def post(self, request):
        # 1. Validate token
        token = request.headers.get('X‑Tracking‑Token')
        if not token:
            return api_response(status.HTTP_401_UNAUTHORIZED, message='Missing tracking token.')

        site = SiteService().get_site_by_token(token)
        if not site:
            return api_response(status.HTTP_401_UNAUTHORIZED, message='Invalid tracking token.')

        # 2. Validate payload
        serializer = EventPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 3. Extract request metadata
        ip = get_client_ip(request)
        ua = get_user_agent(request)

        # 4. Record event
        IngestionService().record_event(
            site_id=site.id,
            payload=serializer.validated_data,
            ip_address=ip,
            user_agent_str=ua,
        )

        return api_response(status.HTTP_204_NO_CONTENT, message='Event recorded.')