from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import decorators, permissions, response, views, viewsets

from .adapters import get_adapter
from .models import Transaction, Wallet
from .serializers import (
    ChargeSerializer,
    PayoutSerializer,
    TransactionSerializer,
    WalletSerializer,
)

User = get_user_model()


class WalletView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return response.Response(WalletSerializer(wallet).data)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == "admin":
            return Transaction.objects.all()
        return Transaction.objects.filter(user=self.request.user)


class ChargeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChargeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        adapter = get_adapter(data["provider"])
        result = adapter.charge(
            phone=data.get("phone") or request.user.phone,
            amount=data["amount"],
            currency=data["currency"],
        )
        txn = Transaction.objects.create(
            user=request.user,
            kind=data["kind"],
            provider=data["provider"],
            amount=data["amount"],
            currency=data["currency"],
            status=result["status"],
            reference=result["reference"],
            appointment_id=data.get("appointment"),
            metadata=result.get("raw", {}),
        )
        return response.Response(TransactionSerializer(txn).data, status=201)


class PayoutView(views.APIView):
    """Overseas Independent Contractor payout via Stripe (international transfer)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role not in {"admin"}:
            return response.Response({"detail": "Admin only."}, status=403)
        serializer = PayoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        provider_user = get_object_or_404(User, pk=data["provider_user"])

        result = get_adapter("stripe").payout(
            destination=data["destination"], amount=data["amount"], currency=data["currency"]
        )
        txn = Transaction.objects.create(
            user=provider_user,
            kind="ic_payout",
            provider="stripe",
            amount=data["amount"],
            currency=data["currency"],
            status=result["status"],
            reference=result["reference"],
            metadata={**result.get("raw", {}), "contract": "non-US IC agreement"},
        )
        return response.Response(TransactionSerializer(txn).data, status=201)
