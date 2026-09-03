from rest_framework import serializers

from .models import StoreAndForwardMessage, VideoSession


class VideoSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoSession
        fields = ("id", "consultation", "provider", "room", "status", "mode", "created_at", "ended_at")


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True)

    class Meta:
        model = StoreAndForwardMessage
        fields = ("id", "consultation", "sender", "sender_name", "body", "attachment_url", "created_at", "delivered")
        read_only_fields = ("sender", "delivered")
