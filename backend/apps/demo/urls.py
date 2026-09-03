from django.urls import path

from .views import DemoSeedView

urlpatterns = [
    path("demo/seed", DemoSeedView.as_view(), name="demo-seed"),
]
