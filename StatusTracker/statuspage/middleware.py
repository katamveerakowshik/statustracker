from django.utils.deprecation import MiddlewareMixin
from .models import Organization, OrganizationMember


class CurrentOrganizationMiddleware(MiddlewareMixin):
    """
    Middleware to handle the current organization.
    Makes current organization available in the request.
    """
    
    def process_request(self, request):
        if not request.user.is_authenticated:
            request.organization = None
            return None
        
        # Get organization from session
        org_id = request.session.get('current_organization_id')
        if org_id:
            try:
                request.organization = Organization.objects.get(
                    id=org_id,
                    members__user=request.user
                )
                return None
            except Organization.DoesNotExist:
                # Organization not found or not a member
                pass
        
        # Try to get first available organization
        try:
            org = Organization.objects.filter(members__user=request.user).first()
            if org:
                request.organization = org
                request.session['current_organization_id'] = org.id
            else:
                request.organization = None
        except:
            request.organization = None
        
        return None
