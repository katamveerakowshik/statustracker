import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Organization, Service, Incident


class StatusUpdateConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for status updates"""
    
    async def connect(self):
        # Get organization from URL
        self.organization_id = self.scope['url_route']['kwargs'].get('organization_id')
        
        # If no organization specified in URL, try to get it from session
        if not self.organization_id:
            self.organization_id = self.scope.get('session', {}).get('current_organization_id')
        
        # Connect to group if organization exists
        if self.organization_id:
            self.group_name = f'status_updates_{self.organization_id}'
            
            # Join group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Send initial status
            await self.send_initial_status()
        else:
            # No organization, reject connection
            await self.close()
    
    async def disconnect(self, close_code):
        # Leave group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        # No incoming messages expected, but handle if needed
        pass
    
    # Send initial status data upon connection
    async def send_initial_status(self):
        data = await self.get_status_data()
        await self.send(text_data=json.dumps(data))
    
    # Receive message from group
    async def status_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event['data']))
    
    @database_sync_to_async
    def get_status_data(self):
        # Get services data
        services = Service.objects.filter(organization_id=self.organization_id)
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
            organization_id=self.organization_id,
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
        
        # Return data
        return {
            'organization_id': self.organization_id,
            'services': services_data,
            'incidents': incidents_data,
            'timestamp': timezone.now().isoformat(),
        }
