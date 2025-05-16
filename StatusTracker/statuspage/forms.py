from django import forms
from .models import Organization, Service, Incident, IncidentUpdate, OrganizationInvitation, Team


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'slug': 'URL-friendly name (lowercase, no spaces, use hyphens)',
        }
        
        
class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class IncidentForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
            'style': 'margin-right: 8px;'
        }),
        required=False
    )
    
    class Meta:
        model = Incident
        fields = ['title', 'type', 'status', 'impact', 'services', 'scheduled_start', 'scheduled_end']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'impact': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'scheduled_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        if organization:
            self.fields['services'].queryset = Service.objects.filter(organization=organization)
        
        # If we're editing an existing instance, set initial services
        instance = kwargs.get('instance')
        if instance:
            self.fields['services'].initial = instance.services.all()


class IncidentUpdateForm(forms.ModelForm):
    class Meta:
        model = IncidentUpdate
        fields = ['message', 'status']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class InvitationForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        help_text='Enter the email address of the person you want to invite'
    )
    role = forms.ChoiceField(
        choices=OrganizationInvitation.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial=OrganizationInvitation.ROLE_VIEWER
    )
    
    class Meta:
        model = OrganizationInvitation
        fields = ['email', 'role']
