from rest_framework.routers import DefaultRouter

from .views import MedicationViewSet, PrescriptionViewSet

router = DefaultRouter(trailing_slash=False)
router.register("prescriptions", PrescriptionViewSet, basename="prescription")
router.register("formulary", MedicationViewSet, basename="medication")

urlpatterns = router.urls
