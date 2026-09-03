from django.urls import path

from .consumers import ConsultationSignalConsumer, PharmacyStatusConsumer

websocket_urlpatterns = [
    path("ws/consultations/<str:room>/signal", ConsultationSignalConsumer.as_asgi()),
    path("ws/pharmacy/status", PharmacyStatusConsumer.as_asgi()),
]
