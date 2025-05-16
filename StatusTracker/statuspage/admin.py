from django.contrib import admin
from .models import Organization, OrganizationMember, Service, Incident, IncidentUpdate

class OrganizationMemberInline(admin.TabularInline):
    model = OrganizationMember
    extra = 1

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    inlines = [OrganizationMemberInline]

@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'created_at')
    list_filter = ('organization', 'role')
    search_fields = ('user__username', 'user__email', 'organization__name')

class IncidentUpdateInline(admin.TabularInline):
    model = IncidentUpdate
    extra = 1

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'status', 'created_at')
    list_filter = ('organization', 'status')
    search_fields = ('name', 'description', 'organization__name')

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'type', 'status', 'created_at')
    list_filter = ('organization', 'type', 'status')
    search_fields = ('title', 'organization__name')
    filter_horizontal = ('services',)
    inlines = [IncidentUpdateInline]

@admin.register(IncidentUpdate)
class IncidentUpdateAdmin(admin.ModelAdmin):
    list_display = ('incident', 'status', 'created_at')
    list_filter = ('status', 'incident__organization')
    search_fields = ('message', 'incident__title', 'incident__organization__name')
