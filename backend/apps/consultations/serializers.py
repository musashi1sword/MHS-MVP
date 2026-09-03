from rest_framework import serializers

from apps.communications.serializers import VideoSessionSerializer

from .models import Consultation


class ConsultationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    provider_name = serializers.CharField(source="provider.get_full_name", read_only=True, default=None)
    video_sessions = VideoSessionSerializer(many=True, read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)

    class Meta:
        model = Consultation
        fields = (
            "id",
            "appointment",
            "patient",
            "patient_name",
            "provider",
            "provider_name",
            "started_at",
            "ended_at",
            "subjective",
            "objective",
            "assessment",
            "plan",
            "note_finalised",
            "duration_seconds",
            "video_sessions",
        )
        read_only_fields = ("patient", "provider", "started_at")


class StartConsultationSerializer(serializers.Serializer):
    appointment = serializers.IntegerField()
    mode = serializers.ChoiceField(choices=["video", "audio"], default="video")
    video_provider = serializers.ChoiceField(
        choices=["webrtc", "managed"], required=False, allow_null=True
    )


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = ("subjective", "objective", "assessment", "plan", "note_finalised")
