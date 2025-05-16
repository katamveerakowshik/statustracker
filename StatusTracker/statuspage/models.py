from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Organization(models.Model):
    """
    Represents an organization with multiple users and services
    (multi-tenant architecture)
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Team(models.Model):
    """
    Represents a team within an organization that manages specific services
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('name', 'organization')
    
    def __str__(self):
        return f"{self.name} - {self.organization.name}"


class OrganizationMember(models.Model):
    """
    Represents a user's membership in an organization with role-based permissions
    """
    ROLE_ADMIN = 'admin'
    ROLE_VIEWER = 'viewer'
    
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_VIEWER, 'Viewer'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_VIEWER)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'organization')
    
    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role})"
    
    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN


class TeamMember(models.Model):
    """
    Represents a user's membership in a team with role-based permissions
    """
    ROLE_MANAGER = 'manager'
    ROLE_MEMBER = 'member'
    
    ROLE_CHOICES = [
        (ROLE_MANAGER, 'Manager'),
        (ROLE_MEMBER, 'Member'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'team')
    
    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"
    
    @property
    def is_manager(self):
        return self.role == self.ROLE_MANAGER
    
    @property
    def can_update_status(self):
        """Team members and managers can update service status"""
        return True


class Service(models.Model):
    """
    Represents a service (e.g., Website, API, Database) that can have a status
    Each service is managed by a specific team within the organization
    """
    STATUS_OPERATIONAL = 'operational'
    STATUS_DEGRADED = 'degraded'
    STATUS_PARTIAL_OUTAGE = 'partial_outage'
    STATUS_MAJOR_OUTAGE = 'major_outage'
    
    STATUS_CHOICES = [
        (STATUS_OPERATIONAL, 'Operational'),
        (STATUS_DEGRADED, 'Degraded Performance'),
        (STATUS_PARTIAL_OUTAGE, 'Partial Outage'),
        (STATUS_MAJOR_OUTAGE, 'Major Outage'),
    ]
    
    SEVERITY_ORDER = {
        STATUS_OPERATIONAL: 0,
        STATUS_DEGRADED: 1,
        STATUS_PARTIAL_OUTAGE: 2,
        STATUS_MAJOR_OUTAGE: 3,
    }
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='services')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, related_name='services', null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPERATIONAL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def status_color(self):
        """Return the Bootstrap color class for the current status"""
        color_map = {
            self.STATUS_OPERATIONAL: 'success',
            self.STATUS_DEGRADED: 'warning',
            self.STATUS_PARTIAL_OUTAGE: 'orange',
            self.STATUS_MAJOR_OUTAGE: 'danger',
        }
        return color_map.get(self.status, 'secondary')

    def recalculate_status(self):
        # Get all active incidents affecting this service
        active_incidents = self.incidents.filter(
            status__in=[
                'investigating', 'identified', 'monitoring', 'scheduled', 'in_progress'
            ]
        )
        if not active_incidents.exists():
            self.status = self.STATUS_OPERATIONAL
        else:
            severities = [self.SEVERITY_ORDER[incident.impact] for incident in active_incidents]
            max_severity = max(severities)
            status_map = {v: k for k, v in self.SEVERITY_ORDER.items()}
            self.status = status_map[max_severity]
        self.save(update_fields=['status'])


class Incident(models.Model):
    """
    Represents an incident or maintenance event affecting one or more services
    """
    TYPE_INCIDENT = 'incident'
    TYPE_MAINTENANCE = 'maintenance'
    
    TYPE_CHOICES = [
        (TYPE_INCIDENT, 'Incident'),
        (TYPE_MAINTENANCE, 'Scheduled Maintenance'),
    ]
    
    STATUS_INVESTIGATING = 'investigating'
    STATUS_IDENTIFIED = 'identified'
    STATUS_MONITORING = 'monitoring'
    STATUS_RESOLVED = 'resolved'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    
    STATUS_CHOICES = [
        (STATUS_INVESTIGATING, 'Investigating'),
        (STATUS_IDENTIFIED, 'Identified'),
        (STATUS_MONITORING, 'Monitoring'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='incidents')
    services = models.ManyToManyField(Service, related_name='incidents')
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_INCIDENT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INVESTIGATING)
    impact = models.CharField(max_length=20, choices=Service.STATUS_CHOICES, default=Service.STATUS_DEGRADED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    @property
    def is_active(self):
        if self.type == self.TYPE_INCIDENT:
            return self.status != self.STATUS_RESOLVED
        else:  # Maintenance
            return self.status != self.STATUS_COMPLETED
    
    @property
    def status_color(self):
        """Return the Bootstrap color class for the current status"""
        color_map = {
            self.STATUS_INVESTIGATING: 'danger',
            self.STATUS_IDENTIFIED: 'warning',
            self.STATUS_MONITORING: 'info',
            self.STATUS_RESOLVED: 'success',
            self.STATUS_SCHEDULED: 'info',
            self.STATUS_IN_PROGRESS: 'warning',
            self.STATUS_COMPLETED: 'success',
        }
        return color_map.get(self.status, 'secondary')


class IncidentUpdate(models.Model):
    """
    Represents an update to an incident with a timestamp and message
    """
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='updates')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Incident.STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Update for {self.incident.title} at {self.created_at}"


class OrganizationInvitation(models.Model):
    """
    Represents an invitation sent to a user to join an organization
    """
    ROLE_ADMIN = 'admin'
    ROLE_VIEWER = 'viewer'
    
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_VIEWER, 'Viewer'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_VIEWER)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    # Optional field to specify which team the user should be added to
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, related_name='invitations', null=True, blank=True)
    
    class Meta:
        unique_together = ('organization', 'email')
    
    def __str__(self):
        return f"Invitation for {self.email} to {self.organization.name}"
    
    def send_invitation_email(self, request=None):
        """
        Send an invitation email using Django's built-in email functionality
        """
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.urls import reverse
        from django.conf import settings
        
        accept_url = reverse('accept_invitation', kwargs={'token': self.token})
        if request:
            accept_url = request.build_absolute_uri(accept_url)
        else:
            # If no request object is provided, construct a URL based on the site domain
            from django.contrib.sites.models import Site
            site = Site.objects.get_current()
            accept_url = f"https://{site.domain}{accept_url}"
            
        context = {
            'invitation': self,
            'accept_url': accept_url,
        }
        
        subject = f"Invitation to join {self.organization.name} on Status Page"
        html_message = render_to_string('statuspage/email/invitation.html', context)
        plain_message = render_to_string('statuspage/email/invitation_text.html', context)
        
        return send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            fail_silently=False,
        )
