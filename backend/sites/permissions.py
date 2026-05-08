from rest_framework import permissions

class IsSiteOwner(permissions.BasePermission):
    """Object-level permission: only the owner can access/modify a site."""
    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id