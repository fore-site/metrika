from rest_framework import permissions
from django.http import Http404

class IsSiteOwner(permissions.BasePermission):
    """Object-level permission: only the owner can access/modify a site."""
    def has_object_permission(self, request, view, obj):
        if obj.user_id != request.user.id:
            raise Http404("Site not found.")  # Hide existence of the site
        return True