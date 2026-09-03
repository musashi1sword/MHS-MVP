from django.urls import path

from .views import MetricsDashboardView

urlpatterns = [
    path("dashboard/metrics", MetricsDashboardView.as_view(), name="dashboard-metrics"),
]
