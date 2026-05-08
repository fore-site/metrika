from rest_framework import generics, permissions, status
from common.response import api_response
from .models import Site
from .services import SiteService
from .serializers import CreateSiteSerializer, UpdateSiteSerializer, SiteSerializer
from .permissions import IsSiteOwner

class SiteListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    # List uses SiteSerializer; Create uses CreateSiteSerializer (set manually)
    serializer_class = SiteSerializer   # for GET (list)

    def get_queryset(self):
        return SiteService().get_sites_for_user(self.request.user.id)

    def create(self, request, *args, **kwargs):
        serializer = CreateSiteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain = serializer.validated_data['domain']

        try:
            site = SiteService().create_site(request.user.id, domain)
        except ValueError as e:
            return api_response(status.HTTP_400_BAD_REQUEST, message=str(e))

        return api_response(
            status.HTTP_201_CREATED,
            data=SiteSerializer(site).data,
            message='Site created successfully.',
        )


class SiteDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSiteOwner]
    queryset = Site.objects.all()    # base queryset; object-level filtered by permission
    serializer_class = SiteSerializer
    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return api_response(status.HTTP_200_OK, data=SiteSerializer(instance).data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = UpdateSiteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            site = SiteService().update_site(
                instance.id,
                request.user.id,
                domain=data.get('domain'),
                is_active=data.get('is_active'),
            )
        except ValueError as e:
            return api_response(status.HTTP_400_BAD_REQUEST, message=str(e))

        if site is None:   # shouldn't happen due to permission check
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')

        return api_response(status.HTTP_200_OK, data=SiteSerializer(site).data, message='Site updated.')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        success = SiteService().deactivate_site(instance.id, request.user.id)
        if not success:
            return api_response(status.HTTP_404_NOT_FOUND, message='Site not found.')
        return api_response(status.HTTP_200_OK, message='Site deactivated.')