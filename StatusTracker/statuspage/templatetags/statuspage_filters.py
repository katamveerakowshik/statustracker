from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def filter_maintenance(incidents):
    """
    Filter incidents to only return maintenance incidents
    """
    return [incident for incident in incidents if incident.type == 'maintenance']

@register.filter
def filter_incidents(incidents):
    """
    Filter incidents to only return non-maintenance incidents
    """
    return [incident for incident in incidents if incident.type == 'incident']

@register.filter
def filter_active_incidents(incidents):
    """
    Filter incidents to only return active incidents
    """
    active_statuses = ['investigating', 'identified', 'monitoring']
    return [incident for incident in incidents if incident.type == 'incident' and incident.status in active_statuses]

@register.filter
def filter_resolved_incidents(incidents):
    """
    Filter incidents to only return resolved incidents
    """
    return [incident for incident in incidents if incident.type == 'incident' and incident.status == 'resolved']

@register.filter
def status_color(status):
    """
    Return a Bootstrap color class based on status
    """
    colors = {
        'operational': 'success',
        'degraded': 'warning',
        'partial_outage': 'warning',
        'major_outage': 'danger',
        'investigating': 'warning',
        'identified': 'warning',
        'monitoring': 'info',
        'resolved': 'success',
        'scheduled': 'info',
        'in_progress': 'warning',
        'completed': 'success'
    }
    return colors.get(status, 'secondary')