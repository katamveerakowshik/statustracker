from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import Service, Incident, IncidentUpdate
from .utils import send_status_update


def update_services_for_incident(incident):
    for service in incident.services.all():
        service.recalculate_status()


@receiver(post_save, sender=Service)
def service_saved(sender, instance, created, **kwargs):
    """
    When a service is created or updated, send status updates
    to all connected WebSocket clients for the organization.
    """
    if instance.organization_id:
        send_status_update(instance.organization_id)


@receiver(post_delete, sender=Service)
def service_deleted(sender, instance, **kwargs):
    """
    When a service is deleted, send status updates
    to all connected WebSocket clients for the organization.
    """
    if instance.organization_id:
        send_status_update(instance.organization_id)


@receiver(post_save, sender=Incident)
def incident_saved(sender, instance, created, **kwargs):
    """
    When an incident is created or updated, update affected services and send status updates.
    """
    update_services_for_incident(instance)
    if instance.organization_id:
        send_status_update(instance.organization_id)


@receiver(post_delete, sender=Incident)
def incident_deleted(sender, instance, **kwargs):
    """
    When an incident is deleted, update affected services and send status updates.
    """
    for service in instance.services.all():
        service.recalculate_status()
    if instance.organization_id:
        send_status_update(instance.organization_id)


@receiver(post_save, sender=IncidentUpdate)
def incident_update_saved(sender, instance, created, **kwargs):
    """
    When an incident update is created, send status updates
    to all connected WebSocket clients for the organization.
    """
    if instance.incident.organization_id:
        send_status_update(instance.incident.organization_id)


@receiver(m2m_changed, sender=Incident.services.through)
def incident_services_changed(sender, instance, action, **kwargs):
    """
    When services are added or removed from an incident, update affected services and send status updates.
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        update_services_for_incident(instance)
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.organization_id:
        send_status_update(instance.organization_id)
