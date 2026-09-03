from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ChargeView, PayoutView, TransactionViewSet, WalletView

router = DefaultRouter(trailing_slash=False)
router.register("transactions", TransactionViewSet, basename="transaction")

urlpatterns = router.urls + [
    path("payments/wallet", WalletView.as_view(), name="wallet"),
    path("payments/charge", ChargeView.as_view(), name="charge"),
    path("payments/payout", PayoutView.as_view(), name="payout"),
]
