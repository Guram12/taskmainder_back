from rest_framework import permissions
from .models import BoardMembership

class IsOwnerOrMember(permissions.BasePermission):
    """
    Custom permission to only allow owners or members of a board to view or edit it.
    """
    def has_object_permission(self, request, view, obj):
        try:
            membership = BoardMembership.objects.get(board=obj, user=request.user)
            return membership.user_status in ['owner', 'admin', 'member']
        except BoardMembership.DoesNotExist:
            return False