from rest_framework import permissions, response, views

from .seed import seed_demo


class DemoSeedView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        return response.Response(seed_demo(), status=201)
