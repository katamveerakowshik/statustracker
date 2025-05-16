from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Organization,
    OrganizationMember,
    Service,
    Incident,
    IncidentUpdate
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'created_at']


class OrganizationMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    
    class Meta:
        model = OrganizationMember
        fields = ['id', 'user', 'organization', 'role', 'created_at']


class ServiceSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_color = serializers.CharField(read_only=True)
    
    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'status', 'status_display', 
                  'status_color', 'organization', 'created_at', 'updated_at']


class IncidentUpdateSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = IncidentUpdate
        fields = ['id', 'message', 'status', 'status_display', 'created_at']


class IncidentSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    services = ServiceSerializer(many=True, read_only=True)
    updates = IncidentUpdateSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    impact_display = serializers.CharField(source='get_impact_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_color = serializers.CharField(read_only=True)
    
    class Meta:
        model = Incident
        fields = ['id', 'title', 'type', 'type_display', 'status', 'status_display',
                  'impact', 'impact_display', 'status_color', 'organization', 
                  'services', 'updates', 'created_at', 'updated_at',
                  'scheduled_start', 'scheduled_end', 'is_active']


class IncidentCreateUpdateSerializer(serializers.ModelSerializer):
    service_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Incident
        fields = ['id', 'title', 'type', 'status', 'impact', 'service_ids',
                  'scheduled_start', 'scheduled_end']
    
    def create(self, validated_data):
        service_ids = validated_data.pop('service_ids', [])
        organization = self.context['organization']
        
        incident = Incident.objects.create(
            organization=organization,
            **validated_data
        )
        
        # Add services to incident
        services = Service.objects.filter(
            organization=organization,
            id__in=service_ids
        )
        incident.services.set(services)
        
        # Create initial update
        IncidentUpdate.objects.create(
            incident=incident,
            status=incident.status,
            message=f"Incident created: {incident.title}"
        )
        
        return incident


class IncidentUpdateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentUpdate
        fields = ['message', 'status']
