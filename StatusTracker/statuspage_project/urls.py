"""
URL Configuration for statuspage_project
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('api/', include('statuspage.urls')),
    path('', include('statuspage.urls')),
]
