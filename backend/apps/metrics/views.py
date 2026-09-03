from rest_framework import permissions, response, views

from .service import build_metrics


class MetricsDashboardView(views.APIView):
    permission_classes = [permissions.AllowAny]  # investor slide, no auth wall for the demo

    def get(self, request):
        return response.Response(build_metrics())
