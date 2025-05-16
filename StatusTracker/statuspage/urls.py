from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from . import views

# API router setup
router = DefaultRouter()
router.register(r'organizations', views.OrganizationViewSet, basename='api-organization')
router.register(r'services', views.ServiceViewSet, basename='api-service')
router.register(r'incidents', views.IncidentViewSet, basename='api-incident')

# Nested routers for incident updates
incident_router = routers.NestedSimpleRouter(router, r'incidents', lookup='incident')
incident_router.register(r'updates', views.IncidentUpdateViewSet, basename='api-incident-update')

urlpatterns = [
    # Public pages
    path('', views.HomeView.as_view(), name='home'),
    path('status/<slug:org_slug>/', views.PublicStatusView.as_view(), name='public_status'),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Organizations
    path('organizations/', views.OrganizationListView.as_view(), name='organization_list'),
    path('organizations/create/', views.OrganizationCreateView.as_view(), name='organization_create'),
    path('organizations/<int:pk>/update/', views.OrganizationUpdateView.as_view(), name='organization_update'),
    path('organizations/set-current/<int:organization_id>/', views.set_current_organization, name='set_current_organization'),
    path('organizations/<int:pk>/members/', views.organization_members, name='organization_members'),
    path('organizations/<int:pk>/invite/', views.organization_invite, name='organization_invite'),
    path('invitations/accept/<uuid:token>/', views.accept_invitation, name='accept_invitation'),
    
    # Services
    path('services/', views.ServiceListView.as_view(), name='service_list'),
    path('services/create/', views.ServiceCreateView.as_view(), name='service_create'),
    path('services/<int:pk>/update/', views.ServiceUpdateView.as_view(), name='service_update'),
    
    # Incidents
    path('incidents/', views.IncidentListView.as_view(), name='incident_list'),
    path('incidents/create/', views.IncidentCreateView.as_view(), name='incident_create'),
    path('incidents/<int:pk>/', views.IncidentDetailView.as_view(), name='incident_detail'),
    path('incidents/<int:pk>/update/', views.IncidentUpdateView.as_view(), name='incident_update'),
    path('incidents/<int:pk>/add-update/', views.add_incident_update, name='add_incident_update'),
    
    # API
    path('api/', include(router.urls)),
    path('api/', include(incident_router.urls)),
]
