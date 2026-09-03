from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import decorators, permissions, response, viewsets

from apps.appointments.models import Appointment, AppointmentStatus
from apps.communications.providers import get_provider

from .models import Consultation
from .serializers import ConsultationSerializer, NoteSerializer, StartConsultationSerializer


class ConsultationViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Consultation.objects.select_related("patient", "provider").prefetch_related(
            "video_sessions"
        )
        if user.role == "patient":
            return qs.filter(patient=user)
        if user.role in {"clinician", "chw"}:
            return qs.filter(provider=user)
        return qs

    @decorators.action(detail=False, methods=["post"], url_path="start")
    def start(self, request):
        """Initiate a consultation + WebRTC (dual-mode) session for an appointment."""
        serializer = StartConsultationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appt = get_object_or_404(Appointment, pk=serializer.validated_data["appointment"])

        provider_user = request.user if request.user.role in {"clinician", "chw"} else appt.provider
        consultation, created = Consultation.objects.get_or_create(
            appointment=appt,
            defaults={"patient": appt.patient, "provider": provider_user},
        )

        # Provider joining marks the appointment as seen / in progress (funnel metric).
        if request.user == appt.provider and appt.seen_at is None:
            appt.seen_at = timezone.now()
            appt.status = AppointmentStatus.IN_PROGRESS
            appt.save(update_fields=["seen_at", "status"])

        video = get_provider(serializer.validated_data.get("video_provider"))
        session = video.create_session(consultation, mode=serializer.validated_data["mode"])
        join = video.join_info(session, request.user)

        return response.Response(
            {
                "consultation": ConsultationSerializer(consultation).data,
                "session_id": session.id,
                "join": join.as_dict(),
            },
            status=201 if created else 200,
        )

    @decorators.action(detail=True, methods=["put", "patch"], url_path="note")
    def note(self, request, pk=None):
        consultation = self.get_object()
        serializer = NoteSerializer(consultation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(ConsultationSerializer(consultation).data)

    @decorators.action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        consultation = self.get_object()
        consultation.ended_at = timezone.now()
        consultation.save(update_fields=["ended_at"])
        for session in consultation.video_sessions.exclude(status="ended"):
            get_provider(session.provider).end_session(session)
        return response.Response(ConsultationSerializer(consultation).data)
