from rest_framework import permissions, viewsets

from .models import Clinic, Pharmacy
from .serializers import ClinicSerializer, PharmacySerializer


class ClinicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Clinic.objects.all().order_by("name")
    serializer_class = ClinicSerializer
    permission_classes = [permissions.AllowAny]


class PharmacyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pharmacy.objects.all().order_by("name")
    serializer_class = PharmacySerializer
    permission_classes = [permissions.AllowAny]
