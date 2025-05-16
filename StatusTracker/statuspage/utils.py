import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Service, Incident


def send_status_update(organization_id):
    """
    Send status update to all connected WebSocket clients for the given organization.
    Used when service status or incidents are updated.
    """
    channel_layer = get_channel_layer()
    
    # Get services data
    services = Service.objects.filter(organization_id=organization_id)
    services_data = []
    
    for service in services:
        services_data.append({
            'id': service.id,
            'name': service.name,
            'status': service.status,
            'status_display': service.get_status_display(),
            'status_color': service.status_color,
        })
    
    # Get active incidents
    incidents = Incident.objects.filter(
        organization_id=organization_id,
        status__in=['investigating', 'identified', 'monitoring', 'scheduled', 'in_progress']
    )
    incidents_data = []
    
    for incident in incidents:
        incidents_data.append({
            'id': incident.id,
            'title': incident.title,
            'status': incident.status,
            'status_display': incident.get_status_display(),
            'status_color': incident.status_color,
            'type': incident.type,
            'type_display': incident.get_type_display(),
            'created_at': incident.created_at.isoformat(),
            'services': [s.id for s in incident.services.all()],
        })
    
    # Prepare update data
    update_data = {
        'organization_id': organization_id,
        'services': services_data,
        'incidents': incidents_data,
    }
    
    # Send to channel group
    async_to_sync(channel_layer.group_send)(
        f'status_updates_{organization_id}',
        {
            'type': 'status.update',
            'data': update_data,
        }
    )
