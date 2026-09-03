from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1 = [
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.clinics.urls")),
    path("", include("apps.appointments.urls")),
    path("", include("apps.consultations.urls")),
    path("", include("apps.prescriptions.urls")),
    path("", include("apps.pharmacy.urls")),
    path("", include("apps.payments.urls")),
    path("", include("apps.communications.urls")),
    path("", include("apps.metrics.urls")),
    path("", include("apps.demo.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
