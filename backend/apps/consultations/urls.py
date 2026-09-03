from rest_framework.routers import DefaultRouter

from .views import ConsultationViewSet

router = DefaultRouter(trailing_slash=False)
router.register("consultations", ConsultationViewSet, basename="consultation")

urlpatterns = router.urls
