from rest_framework import generics, permissions, response, views, viewsets

from .models import StoreAndForwardMessage, VideoSession
from .providers import get_provider
from .serializers import MessageSerializer


class MessageViewSet(viewsets.ModelViewSet):
    """Store-and-forward messaging for a consultation."""

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = StoreAndForwardMessage.objects.select_related("sender")
        consultation = self.request.query_params.get("consultation")
        return qs.filter(consultation_id=consultation) if consultation else qs

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class VideoSessionJoinView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        session = VideoSession.objects.select_related(
            "consultation", "consultation__provider"
        ).get(pk=pk)
        provider = get_provider(session.provider)
        return response.Response(provider.join_info(session, request.user).as_dict())


class VideoSessionEndView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        session = VideoSession.objects.get(pk=pk)
        get_provider(session.provider).end_session(session)
        return response.Response({"status": "ended"})
