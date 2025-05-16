from rest_framework import permissions
from .models import OrganizationMember, Organization


class IsOrganizationMember(permissions.BasePermission):
    """
    Custom permission to check if user is a member of the current organization
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get current organization
        org_id = request.session.get('current_organization_id')
        if not org_id:
            return False
        
        try:
            return OrganizationMember.objects.filter(
                user=request.user,
                organization_id=org_id
            ).exists()
        except OrganizationMember.DoesNotExist:
            return False


class IsOrganizationAdmin(permissions.BasePermission):
    """
    Custom permission to check if user is an admin of the current organization
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get current organization
        org_id = request.session.get('current_organization_id')
        if not org_id:
            return False
        
        try:
            membership = OrganizationMember.objects.get(
                user=request.user,
                organization_id=org_id
            )
            return membership.role == OrganizationMember.ROLE_ADMIN
        except OrganizationMember.DoesNotExist:
            return False
