from django.utils import timezone
from rest_framework import decorators, permissions, response, viewsets
from rest_framework.exceptions import PermissionDenied

from .models import Appointment, AppointmentStatus, ProviderSlot
from .serializers import (
    AppointmentSerializer,
    BookingSerializer,
    IntakeSerializer,
    ProviderSlotSerializer,
)


class ProviderSlotViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProviderSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = ProviderSlot.objects.select_related("provider", "clinic")
        if self.request.query_params.get("available") != "false":
            qs = qs.filter(is_booked=False, start__gte=timezone.now())
        provider = self.request.query_params.get("provider")
        if provider:
            qs = qs.filter(provider_id=provider)
        return qs


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Appointment.objects.select_related("patient", "provider", "clinic")
        if user.role == "patient":
            return qs.filter(patient=user)
        if user.role in {"clinician", "chw"}:
            return qs.filter(provider=user) | qs.filter(provider__isnull=True)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return BookingSerializer
        return AppointmentSerializer

    def perform_create(self, serializer):
        self.created = serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appt = serializer.save()
        return response.Response(AppointmentSerializer(appt).data, status=201)

    @decorators.action(detail=True, methods=["post"])
    def intake(self, request, pk=None):
        appt = self.get_object()
        serializer = IntakeSerializer(appt, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(AppointmentSerializer(appt).data)

    @decorators.action(detail=False, methods=["get"])
    def queue(self, request):
        """Provider queue, ordered by triage priority then arrival."""
        qs = (
            Appointment.objects.filter(
                status__in=[AppointmentStatus.IN_QUEUE, AppointmentStatus.CONFIRMED]
            )
            .select_related("patient", "provider", "clinic")
            .order_by("queued_at", "scheduled_start")
        )
        if request.user.role in {"clinician", "chw"}:
            qs = qs.filter(provider=request.user) | qs.filter(provider__isnull=True)
        data = sorted(
            AppointmentSerializer(qs, many=True).data,
            key=lambda a: (a["triage"].get("priority_level", 3), a["queued_at"] or a["scheduled_start"]),
        )
        return response.Response(data)

    @decorators.action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        appt = self.get_object()
        if request.user.role not in {"clinician", "chw", "admin"}:
            raise PermissionDenied("Only a provider can complete a visit.")
        appt.status = AppointmentStatus.COMPLETED
        appt.completed_at = timezone.now()
        appt.save(update_fields=["status", "completed_at"])
        return response.Response(AppointmentSerializer(appt).data)
