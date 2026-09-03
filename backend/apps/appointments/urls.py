from rest_framework.routers import DefaultRouter

from .views import AppointmentViewSet, ProviderSlotViewSet

router = DefaultRouter(trailing_slash=False)
router.register("appointments", AppointmentViewSet, basename="appointment")
router.register("slots", ProviderSlotViewSet, basename="slot")

urlpatterns = router.urls
