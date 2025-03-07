from rest_framework import permissions

class IsOwnerOrMember(permissions.BasePermission):
    """
    Custom permission to only allow owners or members of a board to view or edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Object-level permission to only allow owners or members of the board to view/edit it.
        return obj.owner == request.user or request.user in obj.members.all()