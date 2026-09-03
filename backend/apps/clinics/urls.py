from rest_framework.routers import DefaultRouter

from .views import ClinicViewSet, PharmacyViewSet

router = DefaultRouter(trailing_slash=False)
router.register("clinics", ClinicViewSet, basename="clinic")
router.register("pharmacies", PharmacyViewSet, basename="pharmacy")

urlpatterns = router.urls
