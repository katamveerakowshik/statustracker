from .models import Organization

def user_organizations(request):
    """
    Context processor that adds the user's organizations and current organization
    to all templates.
    """
    if not request.user.is_authenticated:
        return {
            'user_organizations': [],
            'current_organization': None,
        }
    
    # Get all user's organizations
    organizations = Organization.objects.filter(members__user=request.user)
    
    # Get current organization
    current_org_id = request.session.get('current_organization_id')
    current_organization = None
    
    if current_org_id:
        try:
            current_organization = Organization.objects.get(id=current_org_id)
        except Organization.DoesNotExist:
            pass
    
    # If no current organization set but user has organizations, set the first one
    if not current_organization and organizations.exists():
        current_organization = organizations.first()
        request.session['current_organization_id'] = current_organization.id
    
    return {
        'user_organizations': organizations,
        'current_organization': current_organization,
    }
