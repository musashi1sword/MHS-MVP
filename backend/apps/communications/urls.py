from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MessageViewSet, VideoSessionEndView, VideoSessionJoinView

router = DefaultRouter(trailing_slash=False)
router.register("messages", MessageViewSet, basename="message")

urlpatterns = router.urls + [
    path("video-sessions/<int:pk>/join", VideoSessionJoinView.as_view(), name="video-join"),
    path("video-sessions/<int:pk>/end", VideoSessionEndView.as_view(), name="video-end"),
]
