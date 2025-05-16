from django.urls import path

from statuspage.consumers import StatusUpdateConsumer

websocket_urlpatterns = [
    path('ws/status-updates/', StatusUpdateConsumer.as_asgi()),
]