from django.urls import path

from .views import PharmacyQueueView, PrescriptionStatusView

urlpatterns = [
    path("pharmacy/queue", PharmacyQueueView.as_view(), name="pharmacy-queue"),
    path("pharmacy/prescriptions/<int:pk>/status", PrescriptionStatusView.as_view(), name="pharmacy-status"),
]
