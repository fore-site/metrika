from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from common.response import api_response
from .models import Site
from .services import SiteService
from .serializers import CreateSiteSerializer, UpdateSiteSerializer, SiteSerializer
from .permissions import IsSiteOwner
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

@extend_schema(
    methods=['GET'],
    summary="List sites",
    description="Get a list of a user's active sites.",
    request=None,
    responses=OpenApiResponse(response=SiteSerializer(many=True)),
    examples=[
        OpenApiExample(
            'Default example',
            value={
                'data': [
                    {
                        'id': '1',
                        'domain': 'example.com',
                        'tracking_token': '27b9d6e1-9d39-4f8a-99c2-fb6c4ea4e7df',
                        'is_active': True,
                        'created_at': '2026-05-17T12:34:56Z'
                    }
                ],
                'message': 'Sites retrieved successfully.'
            }
        )
    ]
)
@extend_schema(
    methods=['POST'],
    summary="Create site",
    description="Create a new site.",
    request=CreateSiteSerializer,
    responses=SiteSerializer,
    examples=[
        OpenApiExample(
            'Default example',
            value={
                'data': {
                        'id': '1',
                        'domain': 'example.com',
                        'tracking_token': '27b9d6e1-9d39-4f8a-99c2-fb6c4ea4e7df',
                        'timezone': 'UTC',
                        'is_active': True,
                        'created_at': '2026-05-17T12:34:56Z'
                    },
                'message': 'Site created successfully.'
            },
            response_only=True
        )
    ]
)
class SiteListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = SiteSerializer   # for GET (list)

    def get_queryset(self):
        return SiteService().get_sites_for_user(self.request.user.id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_response(status.HTTP_200_OK, 
                            data=serializer.data, 
                            message='Sites retrieved successfully.')

    def create(self, request, *args, **kwargs):
        serializer = CreateSiteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain = serializer.validated_data['domain']
        timezone = serializer.validated_data.get('timezone', 'UTC')

        try:
            site = SiteService().create_site(request.user.id, domain, timezone)
        except ValueError as e:
            return api_response(status.HTTP_400_BAD_REQUEST, message=str(e))

        return api_response(
            status.HTTP_201_CREATED,
            data=SiteSerializer(site).data,
            message='Site created successfully.',
        )


@extend_schema(
    methods=['GET'],
    summary="Get site",
    description="Get details of a specific site.",
    request=None,
    responses=SiteSerializer,
    examples=[
        OpenApiExample(
            'Default example',
            value={
                'data': {
                        'id': '1',
                        'domain': 'example.com',
                        'tracking_token': '27b9d6e1-9d39-4f8a-99c2-fb6c4ea4e7df',
                        'timezone': 'UTC',
                        'is_active': True,
                        'created_at': '2026-05-17T12:34:56Z'
                    },
                'message': 'Site retrieved successfully.'
            }
        )
    ]
)
@extend_schema(
    methods=['PUT'],
    summary="Update site",
    description="Update the domain or local timezone of a site.",
    request=UpdateSiteSerializer,
    responses=SiteSerializer,
    examples=[
        OpenApiExample(
            'Domain example',
            value={
                'data': {
                        'domain': 'example.org',
                    },
                'message': 'Site domain updated successfully.'
            },
            response_only=True
        ),
        OpenApiExample(
            'Timezone example',
            value={
                'data': {
                        'timezone': 'America/New_York',
                    },
                'message': 'Site timezone updated successfully.'
            },
            response_only=True
        )
    ]
)
@extend_schema(
    methods=['DELETE'],
    summary="Delete site",
    description="Delete a specific site.",
    request=None,
    responses=None,
)
class SiteDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSiteOwner]
    queryset = Site.objects.all()    # base queryset; object-level filtered by permission
    serializer_class = SiteSerializer
    lookup_field = 'id'

    def get(self, request, *args, **kwargs):
        instance = self.queryset.filter(id=self.kwargs['id']).first()
        if not instance:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')
        self.check_object_permissions(request, instance)
        return api_response(status.HTTP_200_OK, 
                            data=SiteSerializer(instance).data, 
                            message='Site retrieved successfully.')

    def put(self, request, *args, **kwargs):
        instance = self.queryset.filter(id=self.kwargs['id']).first()
        if not instance:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')
        self.check_object_permissions(request, instance)
        serializer = UpdateSiteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain = serializer.validated_data.get('domain')
        timezone = serializer.validated_data.get('timezone')

        try:
            site = SiteService().update_site(
                instance.id,
                request.user.id,
                domain=domain,
                timezone=timezone
            )
        except ValueError as e:
            return api_response(status.HTTP_400_BAD_REQUEST, message=str(e))

        if site is None:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        return api_response(status.HTTP_200_OK, 
                            data=SiteSerializer(site).data, 
                            message='Site updated.')

    def delete(self, request, *args, **kwargs):
        instance = self.queryset.filter(id=self.kwargs['id']).first()
        if not instance:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')
        self.check_object_permissions(request, instance)
        success = SiteService().deactivate_site(instance.id, request.user.id)
        if not success:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')
        return api_response(status.HTTP_204_NO_CONTENT)