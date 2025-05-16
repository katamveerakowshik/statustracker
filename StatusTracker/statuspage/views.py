from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Organization,
    OrganizationMember,
    Service,
    Incident,
    IncidentUpdate,
    OrganizationInvitation
)
from .serializers import (
    OrganizationSerializer,
    OrganizationMemberSerializer,
    ServiceSerializer,
    IncidentSerializer,
    IncidentCreateUpdateSerializer,
    IncidentUpdateSerializer,
    IncidentUpdateCreateSerializer
)

from .forms import (
    OrganizationForm,
    ServiceForm,
    IncidentForm,
    IncidentUpdateForm,
    InvitationForm
)
from .permissions import IsOrganizationAdmin, IsOrganizationMember
from .utils import send_status_update


# Helper view functions

@login_required
def organization_members(request, pk):
    """View to display and manage organization members"""
    organization = get_object_or_404(Organization, pk=pk)
    
    # Check if user is a member and has admin role
    try:
        membership = OrganizationMember.objects.get(user=request.user, organization=organization)
        if not membership.role == 'admin':
            messages.error(request, "You need admin permissions to manage members.")
            return redirect('dashboard')
    except OrganizationMember.DoesNotExist:
        messages.error(request, "You are not a member of this organization.")
        return redirect('dashboard')
    
    # Get all members
    members = OrganizationMember.objects.filter(organization=organization)
    
    # Get all pending invitations
    invitations = OrganizationInvitation.objects.filter(organization=organization, accepted=False)
    
    context = {
        'organization': organization,
        'members': members,
        'invitations': invitations,
    }
    
    return render(request, 'statuspage/organization_members.html', context)

@login_required
def organization_invite(request, pk):
    """View to invite new members to the organization"""
    organization = get_object_or_404(Organization, pk=pk)
    
    # Check if user is a member and has admin role
    try:
        membership = OrganizationMember.objects.get(user=request.user, organization=organization)
        if not membership.role == 'admin':
            messages.error(request, "You need admin permissions to invite members.")
            return redirect('dashboard')
    except OrganizationMember.DoesNotExist:
        messages.error(request, "You are not a member of this organization.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            role = form.cleaned_data['role']
            
            # Check if user is already a member
            user_exists = User.objects.filter(email=email).exists()
            if user_exists:
                user = User.objects.get(email=email)
                if OrganizationMember.objects.filter(user=user, organization=organization).exists():
                    messages.error(request, f"User with email {email} is already a member.")
                    return redirect('organization_members', pk=organization.pk)
            
            # Check if invitation already exists
            if OrganizationInvitation.objects.filter(email=email, organization=organization, accepted=False).exists():
                messages.error(request, f"An invitation has already been sent to {email}.")
                return redirect('organization_members', pk=organization.pk)
            
            # Create invitation
            invitation = form.save(commit=False)
            invitation.organization = organization
            invitation.invited_by = request.user
            invitation.save()
            
            # Send invitation email
            invite_url = request.build_absolute_uri(
                reverse('accept_invitation', kwargs={'token': invitation.token})
            )
            
            email_subject = f"Invitation to join {organization.name} Status Page"
            email_message = f"""
            Hello,
            
            You have been invited by {request.user.get_full_name() or request.user.username} to join the {organization.name} Status Page as a {dict(OrganizationInvitation.ROLE_CHOICES).get(invitation.role)}.
            
            Click the link below to accept the invitation:
            {invite_url}
            
            This invitation will expire in 7 days.
            
            Best regards,
            Status Page Team
            """
            
            try:
                send_mail(
                    email_subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False
                )
                messages.success(request, f"Invitation sent to {email}.")
            except Exception as e:
                invitation.delete()
                messages.error(request, f"Failed to send invitation: {str(e)}")
            
            return redirect('organization_members', pk=organization.pk)
    else:
        form = InvitationForm()
    
    context = {
        'organization': organization,
        'form': form,
    }
    
    return render(request, 'statuspage/organization_invite.html', context)

def accept_invitation(request, token):
    """View to accept an invitation to join an organization"""
    try:
        invitation = OrganizationInvitation.objects.get(
            token=token, 
            accepted=False, 
            created_at__gt=timezone.now() - timedelta(days=7)
        )
    except OrganizationInvitation.DoesNotExist:
        messages.error(request, "This invitation is invalid or has expired.")
        return redirect('home')
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to accept the invitation.")
            return redirect('account_login')
        
        # Check if user is already a member
        if OrganizationMember.objects.filter(
            user=request.user, 
            organization=invitation.organization
        ).exists():
            messages.warning(request, "You are already a member of this organization.")
        else:
            # Create new membership
            OrganizationMember.objects.create(
                user=request.user,
                organization=invitation.organization,
                role=invitation.role
            )
            messages.success(request, 
                f"You have successfully joined {invitation.organization.name} as a {dict(OrganizationInvitation.ROLE_CHOICES).get(invitation.role)}."
            )
        
        # Mark invitation as accepted
        invitation.accepted = True
        invitation.save()
        
        # Set as current organization
        request.session['current_organization'] = invitation.organization.id
        
        return redirect('dashboard')
    
    context = {
        'invitation': invitation,
    }
    return render(request, 'statuspage/accept_invitation.html', context)
def get_current_organization(request):
    """Get the current organization from the session or the first available one"""
    if not request.user.is_authenticated:
        return None
    
    org_id = request.session.get('current_organization_id')
    if org_id:
        try:
            return Organization.objects.get(id=org_id, members__user=request.user)
        except Organization.DoesNotExist:
            pass
    
    # Get the first organization
    try:
        return Organization.objects.filter(members__user=request.user).first()
    except:
        return None


def set_current_organization(request, organization_id):
    """Set the current organization in the session"""
    if request.user.is_authenticated:
        try:
            organization = Organization.objects.get(id=organization_id, members__user=request.user)
            request.session['current_organization_id'] = organization.id
            return JsonResponse({'status': 'success'})
        except Organization.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Organization not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Not authenticated'}, status=401)


# Public views
class HomeView(TemplateView):
    template_name = 'home.html'


class PublicStatusView(TemplateView):
    template_name = 'public/status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        org_slug = self.kwargs.get('org_slug')
        try:
            organization = Organization.objects.get(slug=org_slug)
            
            context['organization'] = organization
            context['services'] = Service.objects.filter(organization=organization)
            
            # Get active incidents
            active_incidents = Incident.objects.filter(
                organization=organization,
                status__in=['investigating', 'identified', 'monitoring', 'scheduled', 'in_progress']
            ).prefetch_related('services', 'updates')
            
            # Get resolved incidents in the last 7 days
            resolved_incidents = Incident.objects.filter(
                organization=organization,
                status__in=['resolved', 'completed'],
                updated_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).prefetch_related('services', 'updates')
            
            context['active_incidents'] = active_incidents
            context['resolved_incidents'] = resolved_incidents
            
        except Organization.DoesNotExist:
            context['organization'] = None
            context['services'] = []
            context['active_incidents'] = []
            context['resolved_incidents'] = []
        
        return context


# Dashboard views
@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        organization = get_current_organization(self.request)
        if organization:
            context['organization'] = organization
            
            # Get services
            context['services'] = Service.objects.filter(organization=organization)
            
            # Get active incidents
            context['active_incidents'] = Incident.objects.filter(
                organization=organization,
                status__in=['investigating', 'identified', 'monitoring', 'scheduled', 'in_progress']
            ).order_by('-created_at')[:5]
            
            # Get recent resolved incidents
            context['resolved_incidents'] = Incident.objects.filter(
                organization=organization,
                status__in=['resolved', 'completed']
            ).order_by('-updated_at')[:5]
            
        return context


# Organization Views
@method_decorator(login_required, name='dispatch')
class OrganizationListView(ListView):
    model = Organization
    template_name = 'organizations/list.html'
    context_object_name = 'organizations'
    
    def get_queryset(self):
        return Organization.objects.filter(members__user=self.request.user)


@method_decorator(login_required, name='dispatch')
class OrganizationCreateView(CreateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/form.html'
    success_url = reverse_lazy('organization_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Create the admin membership for the current user
        OrganizationMember.objects.create(
            user=self.request.user,
            organization=self.object,
            role=OrganizationMember.ROLE_ADMIN
        )
        
        # Set as current organization
        self.request.session['current_organization_id'] = self.object.id
        
        messages.success(self.request, f'Organization "{self.object.name}" created successfully!')
        return response


@method_decorator(login_required, name='dispatch')
class OrganizationUpdateView(UpdateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/form.html'
    success_url = reverse_lazy('organization_list')
    
    def get_queryset(self):
        return Organization.objects.filter(
            members__user=self.request.user, 
            members__role=OrganizationMember.ROLE_ADMIN
        )
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Organization "{self.object.name}" updated successfully!')
        return response


# Service Views
@method_decorator(login_required, name='dispatch')
class ServiceListView(ListView):
    model = Service
    template_name = 'services/list.html'
    context_object_name = 'services'
    
    def get_queryset(self):
        organization = get_current_organization(self.request)
        if organization:
            return Service.objects.filter(organization=organization)
        return Service.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = get_current_organization(self.request)
        return context


@method_decorator(login_required, name='dispatch')
class ServiceCreateView(CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/form.html'
    
    def get_success_url(self):
        return reverse('service_list')
    
    def form_valid(self, form):
        organization = get_current_organization(self.request)
        if not organization:
            messages.error(self.request, "You need to have an organization first")
            return self.form_invalid(form)
        
        # Check if user is admin
        try:
            membership = OrganizationMember.objects.get(
                user=self.request.user, 
                organization=organization
            )
            if not membership.is_admin:
                messages.error(self.request, "You don't have permission to create services")
                return self.form_invalid(form)
        except OrganizationMember.DoesNotExist:
            messages.error(self.request, "You don't have permission to create services")
            return self.form_invalid(form)
        
        form.instance.organization = organization
        response = super().form_valid(form)
        
        messages.success(self.request, f'Service "{form.instance.name}" created successfully!')
        
        # Send status update via WebSockets
        send_status_update(organization.id)
        
        return response


@method_decorator(login_required, name='dispatch')
class ServiceUpdateView(UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/form.html'
    
    def get_success_url(self):
        return reverse('service_list')
    
    def get_queryset(self):
        organization = get_current_organization(self.request)
        if organization:
            try:
                membership = OrganizationMember.objects.get(
                    user=self.request.user, 
                    organization=organization
                )
                if membership.is_admin:
                    return Service.objects.filter(organization=organization)
            except OrganizationMember.DoesNotExist:
                pass
        return Service.objects.none()
    
    def form_valid(self, form):
        previous_status = Service.objects.get(pk=self.object.pk).status
        response = super().form_valid(form)
        
        messages.success(self.request, f'Service "{form.instance.name}" updated successfully!')
        
        # If status changed, send update via WebSockets
        if previous_status != form.instance.status:
            send_status_update(form.instance.organization.id)
        
        return response


# Incident Views
@method_decorator(login_required, name='dispatch')
class IncidentListView(ListView):
    model = Incident
    template_name = 'incidents/list.html'
    context_object_name = 'incidents'
    
    def get_queryset(self):
        organization = get_current_organization(self.request)
        if organization:
            return Incident.objects.filter(organization=organization).order_by('-created_at')
        return Incident.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = get_current_organization(self.request)
        return context


@method_decorator(login_required, name='dispatch')
class IncidentDetailView(DetailView):
    model = Incident
    template_name = 'incidents/detail.html'
    context_object_name = 'incident'
    
    def get_queryset(self):
        organization = get_current_organization(self.request)
        if organization:
            return Incident.objects.filter(organization=organization)
        return Incident.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = get_current_organization(self.request)
        context['update_form'] = IncidentUpdateForm()
        context['updates'] = self.object.updates.all().order_by('-created_at')
        return context


@method_decorator(login_required, name='dispatch')
class IncidentCreateView(CreateView):
    model = Incident
    form_class = IncidentForm
    template_name = 'incidents/form.html'
    
    def get_success_url(self):
        return reverse('incident_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        organization = get_current_organization(self.request)
        kwargs['organization'] = organization
        return kwargs
    
    def form_valid(self, form):
        organization = get_current_organization(self.request)
        if not organization:
            messages.error(self.request, "You need to have an organization first")
            return self.form_invalid(form)
        
        # Check if user is admin
        try:
            membership = OrganizationMember.objects.get(
                user=self.request.user, 
                organization=organization
            )
            if not membership.is_admin:
                messages.error(self.request, "You don't have permission to create incidents")
                return self.form_invalid(form)
        except OrganizationMember.DoesNotExist:
            messages.error(self.request, "You don't have permission to create incidents")
            return self.form_invalid(form)
        
        form.instance.organization = organization
        response = super().form_valid(form)
        
        # Create the initial update
        IncidentUpdate.objects.create(
            incident=self.object,
            status=self.object.status,
            message=f"Incident created: {self.object.title}"
        )
        
        messages.success(self.request, f'Incident "{form.instance.title}" created successfully!')
        
        # Send status update via WebSockets
        send_status_update(organization.id)
        
        return response


@method_decorator(login_required, name='dispatch')
class IncidentUpdateView(UpdateView):
    model = Incident
    form_class = IncidentForm
    template_name = 'incidents/form.html'
    
    def get_success_url(self):
        return reverse('incident_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        organization = get_current_organization(self.request)
        kwargs['organization'] = organization
        return kwargs
    
    def get_queryset(self):
        organization = get_current_organization(self.request)
        if organization:
            try:
                membership = OrganizationMember.objects.get(
                    user=self.request.user, 
                    organization=organization
                )
                if membership.is_admin:
                    return Incident.objects.filter(organization=organization)
            except OrganizationMember.DoesNotExist:
                pass
        return Incident.objects.none()
    
    def form_valid(self, form):
        previous_status = Incident.objects.get(pk=self.object.pk).status
        response = super().form_valid(form)
        
        # If status changed, create an update
        if previous_status != form.instance.status:
            IncidentUpdate.objects.create(
                incident=self.object,
                status=self.object.status,
                message=f"Status changed from {previous_status} to {self.object.status}"
            )
            
            # Send status update via WebSockets
            send_status_update(form.instance.organization.id)
        
        messages.success(self.request, f'Incident "{form.instance.title}" updated successfully!')
        return response


@login_required
def add_incident_update(request, pk):
    incident = get_object_or_404(Incident, pk=pk)
    organization = get_current_organization(request)
    
    # Check if user has permission
    try:
        membership = OrganizationMember.objects.get(
            user=request.user, 
            organization=organization
        )
        if not membership.is_admin:
            messages.error(request, "You don't have permission to update incidents")
            return redirect('incident_detail', pk=pk)
    except OrganizationMember.DoesNotExist:
        messages.error(request, "You don't have permission to update incidents")
        return redirect('incident_detail', pk=pk)
    
    if request.method == 'POST':
        form = IncidentUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.incident = incident
            update.save()
            
            # Update incident status if changed
            if update.status != incident.status:
                incident.status = update.status
                incident.save()
            
            # Send status update via WebSockets
            send_status_update(organization.id)
            
            messages.success(request, "Update added successfully!")
        else:
            messages.error(request, "Error adding update")
    
    return redirect('incident_detail', pk=pk)


# API Views
class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Organization.objects.filter(members__user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_current(self, request, pk=None):
        organization = self.get_object()
        request.session['current_organization_id'] = organization.id
        return Response({'status': 'success'})


class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]
    
    def get_queryset(self):
        organization = get_current_organization(self.request)
        if organization:
            return Service.objects.filter(organization=organization)
        return Service.objects.none()
    
    def perform_create(self, serializer):
        organization = get_current_organization(self.request)
        serializer.save(organization=organization)
        send_status_update(organization.id)
    
    def perform_update(self, serializer):
        old_status = self.get_object().status
        service = serializer.save()
        if old_status != service.status:
            send_status_update(service.organization.id)


class IncidentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return IncidentCreateUpdateSerializer
        return IncidentSerializer
    
    def get_queryset(self):
        organization = get_current_organization(self.request)
        if organization:
            return Incident.objects.filter(organization=organization)
        return Incident.objects.none()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = get_current_organization(self.request)
        return context
    
    def perform_create(self, serializer):
        organization = get_current_organization(self.request)
        incident = serializer.save()
        send_status_update(organization.id)
    
    def perform_update(self, serializer):
        old_status = self.get_object().status
        incident = serializer.save()
        if old_status != incident.status:
            # Create an update for the status change
            IncidentUpdate.objects.create(
                incident=incident,
                status=incident.status,
                message=f"Status changed from {old_status} to {incident.status}"
            )
            send_status_update(incident.organization.id)


class IncidentUpdateViewSet(viewsets.ModelViewSet):
    serializer_class = IncidentUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationAdmin]
    
    def get_queryset(self):
        organization = get_current_organization(self.request)
        if organization:
            incident_id = self.kwargs.get('incident_pk')
            return IncidentUpdate.objects.filter(
                incident__organization=organization,
                incident_id=incident_id
            )
        return IncidentUpdate.objects.none()
    
    def create(self, request, *args, **kwargs):
        incident_id = self.kwargs.get('incident_pk')
        organization = get_current_organization(self.request)
        
        # Check if incident exists and belongs to the organization
        try:
            incident = Incident.objects.get(
                id=incident_id, 
                organization=organization
            )
        except Incident.DoesNotExist:
            return Response(
                {'detail': 'Incident not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = IncidentUpdateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the update
        update = IncidentUpdate.objects.create(
            incident=incident,
            status=serializer.validated_data['status'],
            message=serializer.validated_data['message']
        )
        
        # Update incident status if it changed
        if update.status != incident.status:
            incident.status = update.status
            incident.save()
            send_status_update(organization.id)
        
        return Response(
            IncidentUpdateSerializer(update).data, 
            status=status.HTTP_201_CREATED
        )
